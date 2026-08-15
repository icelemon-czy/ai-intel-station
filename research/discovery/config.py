from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any

import yaml

from collect.papers import AI_CATEGORIES
from collect.wechat import normalize_wechat_url
from collect.hackernews import SUPPORTED_FEEDS


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "discovery.yaml"
EXAMPLE_CONFIG_PATH = REPO_ROOT / "config" / "discovery.yaml.example"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"
DEFAULT_LOG_DIR = REPO_ROOT / ".state" / "discovery"


class DiscoveryConfigError(ValueError):
    """Raised when a discovery YAML cannot be parsed or validated."""


@dataclass
class ConfigError:
    """A single validation problem with the user's YAML."""

    path: str
    message: str
    line: int | None = None
    column: int | None = None

    def format(self) -> str:
        if self.line is not None and self.column is not None:
            return f"  • {self.path}: {self.message} (line {self.line}, col {self.column})"
        if self.line is not None:
            return f"  • {self.path}: {self.message} (line {self.line})"
        return f"  • {self.path}: {self.message}"


@dataclass
class GitHubSearchQuery:
    query: str
    limit: int = 10


@dataclass
class GitHubSource:
    enabled: bool = True
    repos: list[str] = field(default_factory=list)
    search: list[GitHubSearchQuery] = field(default_factory=list)


@dataclass
class PapersSource:
    enabled: bool = True
    categories: list[str] = field(default_factory=list)
    max_per_category: int = 10


@dataclass
class WeChatAccount:
    name: str
    wechat_id: str


@dataclass
class WeChatSource:
    enabled: bool = False
    urls: list[str] = field(default_factory=list)
    accounts: list[WeChatAccount] = field(default_factory=list)
    index_limit: int = 10


@dataclass
class HackerNewsSource:
    enabled: bool = True
    feeds: list[str] = field(default_factory=lambda: ["newstories", "showstories"])
    keywords: list[str] = field(default_factory=list)
    limit: int = 20


@dataclass
class XSource:
    enabled: bool = False
    queries: list[str] = field(default_factory=list)
    token_env: str = "X_BEARER_TOKEN"
    limit: int = 10


@dataclass
class SourceConfig:
    github: GitHubSource = field(default_factory=GitHubSource)
    papers: PapersSource = field(default_factory=PapersSource)
    wechat: WeChatSource = field(default_factory=WeChatSource)
    hackernews: HackerNewsSource = field(default_factory=HackerNewsSource)
    x: XSource = field(default_factory=XSource)


@dataclass
class BriefingConfig:
    enabled: bool = True
    mode: str = "signals"
    keyword: str = "daily"
    sources: list[str] = field(
        default_factory=lambda: ["wechat", "hackernews", "x", "github", "papers"]
    )
    since_days: int = 1
    freshness_hours: int = 48
    # ``max_items`` is retained for legacy signals YAML. New/default signals
    # configs use the four explicit lane fields below.
    max_items: int = 5
    news_items: int = 5
    wechat_min_items: int = 2
    github_items: int = 1
    paper_items: int = 1
    quota_mode: bool = True


@dataclass
class LimitsConfig:
    max_github_search_calls: int = 5
    max_paper_categories: int = 5
    skip_if_already_collected_hours: int = 20
    max_log_files: int = 30


@dataclass
class DiscoveryConfig:
    output_root: Path = field(default_factory=lambda: DEFAULT_OUTPUT_ROOT)
    log_dir: Path = field(default_factory=lambda: DEFAULT_LOG_DIR)
    sources: SourceConfig = field(default_factory=SourceConfig)
    briefing: BriefingConfig = field(default_factory=BriefingConfig)
    limits: LimitsConfig = field(default_factory=LimitsConfig)

    def __post_init__(self) -> None:
        self.output_root = _resolve_path(self.output_root, default=DEFAULT_OUTPUT_ROOT)
        self.log_dir = _resolve_path(self.log_dir, default=DEFAULT_LOG_DIR)


# ---------------------------------------------------------------------------
# Error accumulation
# ---------------------------------------------------------------------------


class _ErrorBag:
    """Accumulates :class:`ConfigError` objects during a config load."""

    def __init__(self) -> None:
        self.errors: list[ConfigError] = []

    def add(self, path: str, message: str, *, line: int | None = None, column: int | None = None) -> None:
        self.errors.append(ConfigError(path=path, message=message, line=line, column=column))

    def raise_if_any(self) -> None:
        if not self.errors:
            return
        bullet_lines = "\n".join(err.format() for err in self.errors)
        raise DiscoveryConfigError(
            f"{len(self.errors)} validation problem(s) in discovery config:\n{bullet_lines}"
        )


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _resolve_path(value: Any, *, default: Path) -> Path:
    if value is None or value == "":
        return Path(default)
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


# ---------------------------------------------------------------------------
# YAML loading with line/column tracking
# ---------------------------------------------------------------------------


class _LocatingLoader(yaml.SafeLoader):
    """A SafeLoader that records ``(line, column)`` for every scalar node.

    We only need scalars (leaves) for error reporting — collection nodes
    inherit location from their first child when relevant.
    """


def _construct_mapping_with_loc(loader: _LocatingLoader, node: yaml.MappingNode) -> dict:
    loader.flatten_mapping(node)
    pairs = loader.construct_pairs(node, deep=True)
    mapping: dict = dict(pairs)
    mapping["__line__"] = node.start_mark.line + 1
    mapping["__col__"] = node.start_mark.column + 1
    return mapping


def _construct_sequence_with_loc(loader: _LocatingLoader, node: yaml.SequenceNode) -> list:
    value = loader.construct_sequence(node, deep=True)
    # We can't decorate the list itself (mutating); instead keep an attribute
    # the parent mapping reads. For our use case we only ever look up the
    # first scalar in a sequence, so the parent's own line/column suffices.
    return value


def _construct_scalar_with_loc(loader: _LocatingLoader, node: yaml.ScalarNode) -> Any:
    value = loader.construct_scalar(node)
    # Stash location on the parent dict in our parser via side-channel.
    setattr(loader, "_last_scalar", (node.start_mark.line + 1, node.start_mark.column + 1))
    return value


_LocatingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_with_loc,
)
_LocatingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    _construct_scalar_with_loc,
)


def _loc(value: Any) -> tuple[int | None, int | None]:
    if isinstance(value, dict):
        return value.get("__line__"), value.get("__col__")
    return None, None


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def _as_mapping(raw: Any, *, where: str, errors: _ErrorBag, line: int | None = None) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        errors.add(where, f"must be a mapping, got {type(raw).__name__}", line=line)
        return {}
    return raw


def _as_list(
    raw: Any,
    *,
    where: str,
    errors: _ErrorBag,
    line: int | None = None,
) -> list:
    if raw is None:
        return []
    if not isinstance(raw, list):
        errors.add(where, f"must be a list, got {type(raw).__name__}", line=line)
        return []
    return raw


def _parse_github(raw: Any, errors: _ErrorBag) -> GitHubSource:
    line, _ = _loc(raw)
    data = _as_mapping(raw, where="sources.github", errors=errors, line=line)
    repos_line, _ = _loc(data.get("repos"))
    repos: list[str] = []
    for index, item in enumerate(
        _as_list(data.get("repos"), where="sources.github.repos", errors=errors, line=repos_line)
    ):
        item_line, _ = _loc(item)
        # Reject non-string entries (a common YAML typo is a mapping or
        # a list where a string is expected). The previous code called
        # str({...}) which produced a noisy representation and let
        # the bad entry through to the GitHub CLI.
        if not isinstance(item, str):
            errors.add(
                f"sources.github.repos[{index}]",
                f"must be a string, got {type(item).__name__}",
                line=item_line,
            )
            continue
        cleaned = item.strip()
        if cleaned:
            repos.append(cleaned)
    search_raw = _as_list(data.get("search"), where="sources.github.search", errors=errors)
    search: list[GitHubSearchQuery] = []
    for index, item in enumerate(search_raw):
        if not isinstance(item, dict):
            errors.add(f"sources.github.search[{index}]", f"must be a mapping, got {type(item).__name__}")
            continue
        item_line, _ = _loc(item)
        query_raw = item.get("query", "")
        query = str(query_raw or "").strip()
        if not query:
            errors.add(
                f"sources.github.search[{index}].query",
                "is required (non-empty string)",
                line=item_line,
            )
        limit_raw = item.get("limit", 10)
        try:
            limit = int(limit_raw)
        except (TypeError, ValueError):
            errors.add(
                f"sources.github.search[{index}].limit",
                f"must be a positive integer, got {limit_raw!r}",
                line=item_line,
            )
            limit = -1
        if limit <= 0 and not any(err.path.endswith(".limit") for err in errors.errors):
            errors.add(
                f"sources.github.search[{index}].limit",
                f"must be positive, got {limit}",
                line=item_line,
            )
        if query:
            search.append(GitHubSearchQuery(query=query, limit=limit if limit > 0 else 10))

    return GitHubSource(
        enabled=bool(data.get("enabled", True)),
        repos=repos,
        search=search,
    )


def _parse_papers(raw: Any, errors: _ErrorBag) -> PapersSource:
    line, _ = _loc(raw)
    data = _as_mapping(raw, where="sources.papers", errors=errors, line=line)
    cats_line, _ = _loc(data.get("categories"))
    raw_categories = _as_list(
        data.get("categories"), where="sources.papers.categories", errors=errors, line=cats_line
    )
    categories: list[str] = []
    for index, item in enumerate(raw_categories):
        item_line, _ = _loc(item)
        if not isinstance(item, str):
            errors.add(
                f"sources.papers.categories[{index}]",
                f"must be a string, got {type(item).__name__}",
                line=item_line,
            )
            continue
        cleaned = item.strip()
        if cleaned:
            categories.append(cleaned)
    unknown = [cat for cat in categories if cat not in AI_CATEGORIES]
    if unknown:
        errors.add(
            "sources.papers.categories",
            f"contains unsupported values: {', '.join(unknown)} "
            f"(supported: {', '.join(AI_CATEGORIES)})",
            line=cats_line,
        )
    max_raw = data.get("max_per_category", 10)
    max_line, _ = _loc(data.get("max_per_category"))
    try:
        max_per_category = int(max_raw)
        if max_per_category <= 0:
            errors.add(
                "sources.papers.max_per_category",
                f"must be positive, got {max_per_category}",
                line=max_line,
            )
    except (TypeError, ValueError):
        errors.add(
            "sources.papers.max_per_category",
            f"must be a positive integer, got {max_raw!r}",
            line=max_line,
        )
        max_per_category = 10
    return PapersSource(
        enabled=bool(data.get("enabled", True)),
        categories=categories,
        max_per_category=max_per_category,
    )


def _parse_wechat(raw: Any, errors: _ErrorBag) -> WeChatSource:
    line, _ = _loc(raw)
    data = _as_mapping(raw, where="sources.wechat", errors=errors, line=line)
    raw_urls = _as_list(data.get("urls"), where="sources.wechat.urls", errors=errors)
    cleaned: list[str] = []
    for index, raw_url in enumerate(raw_urls):
        if not isinstance(raw_url, str):
            errors.add(
                f"sources.wechat.urls[{index}]",
                f"must be a string, got {type(raw_url).__name__}",
            )
            continue
        url = normalize_wechat_url(raw_url)
        if not url:
            continue
        if not url.startswith("https://mp.weixin.qq.com/"):
            errors.add(
                f"sources.wechat.urls[{index}]",
                f"is not a valid mp.weixin.qq.com URL: {raw_url!r}",
            )
            continue
        cleaned.append(url)
    raw_accounts = _as_list(
        data.get("accounts"), where="sources.wechat.accounts", errors=errors
    )
    accounts: list[WeChatAccount] = []
    for index, raw_account in enumerate(raw_accounts):
        if not isinstance(raw_account, dict):
            errors.add(
                f"sources.wechat.accounts[{index}]",
                f"must be a mapping, got {type(raw_account).__name__}",
            )
            continue
        name = str(raw_account.get("name") or "").strip()
        wechat_id = str(raw_account.get("wechat_id") or "").strip()
        if not name or not wechat_id:
            errors.add(
                f"sources.wechat.accounts[{index}]",
                "requires non-empty name and wechat_id",
            )
            continue
        accounts.append(WeChatAccount(name=name, wechat_id=wechat_id))
    index_limit_raw = data.get("index_limit", 10)
    try:
        index_limit = int(index_limit_raw)
    except (TypeError, ValueError):
        index_limit = -1
    if index_limit <= 0 or index_limit > 20:
        errors.add(
            "sources.wechat.index_limit",
            f"must be between 1 and 20, got {index_limit_raw!r}",
        )
        index_limit = 10
    return WeChatSource(
        enabled=bool(data.get("enabled", False)),
        urls=cleaned,
        accounts=accounts,
        index_limit=index_limit,
    )


def _parse_hackernews(raw: Any, errors: _ErrorBag) -> HackerNewsSource:
    # A missing block belongs to an existing pre-signal config. Keep it
    # disabled so loading an old YAML never silently adds a new network call;
    # newly initialized configs opt in explicitly through the checked-in
    # example template.
    if raw is None:
        return HackerNewsSource(enabled=False)
    data = _as_mapping(raw, where="sources.hackernews", errors=errors)
    feeds: list[str] = []
    for index, item in enumerate(
        _as_list(data.get("feeds"), where="sources.hackernews.feeds", errors=errors)
    ):
        if not isinstance(item, str):
            errors.add(
                f"sources.hackernews.feeds[{index}]",
                f"must be a string, got {type(item).__name__}",
            )
            continue
        feed = item.strip()
        if feed not in SUPPORTED_FEEDS:
            errors.add(
                "sources.hackernews.feeds",
                f"contains unsupported value {feed!r} (supported: {', '.join(SUPPORTED_FEEDS)})",
            )
            continue
        if feed not in feeds:
            feeds.append(feed)
    keywords: list[str] = []
    for index, item in enumerate(
        _as_list(data.get("keywords"), where="sources.hackernews.keywords", errors=errors)
    ):
        if not isinstance(item, str):
            errors.add(
                f"sources.hackernews.keywords[{index}]",
                f"must be a string, got {type(item).__name__}",
            )
            continue
        keyword = item.strip()
        if keyword and keyword not in keywords:
            keywords.append(keyword)
    limit_raw = data.get("limit", 20)
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        limit = -1
    if limit <= 0 or limit > 100:
        errors.add(
            "sources.hackernews.limit", f"must be between 1 and 100, got {limit_raw!r}"
        )
        limit = 20
    return HackerNewsSource(
        enabled=bool(data.get("enabled", True)),
        feeds=feeds if data.get("feeds") is not None else ["newstories", "showstories"],
        keywords=keywords,
        limit=limit,
    )


def _parse_x(raw: Any, errors: _ErrorBag) -> XSource:
    data = _as_mapping(raw, where="sources.x", errors=errors)
    queries: list[str] = []
    for index, item in enumerate(
        _as_list(data.get("queries"), where="sources.x.queries", errors=errors)
    ):
        if not isinstance(item, str):
            errors.add(
                f"sources.x.queries[{index}]",
                f"must be a string, got {type(item).__name__}",
            )
            continue
        query = item.strip()
        if query:
            queries.append(query)
    token_env = str(data.get("token_env") or "X_BEARER_TOKEN").strip()
    if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", token_env):
        errors.add(
            "sources.x.token_env",
            f"must be an uppercase environment variable name, got {token_env!r}",
        )
        token_env = "X_BEARER_TOKEN"
    limit_raw = data.get("limit", 10)
    try:
        limit = int(limit_raw)
    except (TypeError, ValueError):
        limit = -1
    if limit < 10 or limit > 100:
        errors.add("sources.x.limit", f"must be between 10 and 100, got {limit_raw!r}")
        limit = 10
    return XSource(
        enabled=bool(data.get("enabled", False)),
        queries=queries,
        token_env=token_env,
        limit=limit,
    )


def _parse_briefing(raw: Any, errors: _ErrorBag) -> BriefingConfig:
    line, _ = _loc(raw)
    data = _as_mapping(raw, where="briefing", errors=errors, line=line)
    mode_line, _ = _loc(data.get("mode"))
    mode = str(data.get("mode", "signals")).strip()
    if mode and mode not in ("signals", "digest", "reading-list"):
        errors.add(
            "briefing.mode",
            f"must be 'signals', 'digest' or 'reading-list', got {mode!r}",
            line=mode_line,
        )
        mode = "signals"
    sources_provided = "sources" in data
    sources_line, _ = _loc(data.get("sources"))
    raw_sources = _as_list(data.get("sources"), where="briefing.sources", errors=errors, line=sources_line)
    sources: list[str] = []
    for source in raw_sources:
        if not isinstance(source, str):
            errors.add(
                "briefing.sources",
                f"contains non-string value: {type(source).__name__} "
                f"(use a YAML string, not a bare number or list)",
                line=sources_line,
            )
            continue
        s = source.strip()
        if not s:
            continue
        if s not in ("github", "papers", "wechat", "hackernews", "x"):
            errors.add(
                "briefing.sources",
                f"contains unsupported value: {s!r} (use github|papers|wechat|hackernews|x)",
                line=sources_line,
            )
        elif s not in sources:
            sources.append(s)
    since_line, _ = _loc(data.get("since_days"))
    since_raw = data.get("since_days", 1)
    try:
        since_days = int(since_raw)
        if since_days <= 0:
            errors.add(
                "briefing.since_days",
                f"must be positive, got {since_days}",
                line=since_line,
            )
            since_days = 1
    except (TypeError, ValueError):
        errors.add(
            "briefing.since_days",
            f"must be a positive integer, got {since_raw!r}",
            line=since_line,
        )
        since_days = 1
    keyword_raw = data.get("keyword", "daily")
    keyword = str(keyword_raw or "daily").strip() or "daily"
    freshness_raw = data.get("freshness_hours", 48)
    try:
        freshness_hours = int(freshness_raw)
    except (TypeError, ValueError):
        freshness_hours = -1
    if freshness_hours <= 0 or freshness_hours > 72:
        errors.add(
            "briefing.freshness_hours",
            f"must be between 1 and 72, got {freshness_raw!r}",
        )
        freshness_hours = 48
    quota_fields = ("news_items", "wechat_min_items", "github_items", "paper_items")
    has_legacy_max = "max_items" in data
    has_quota_fields = any(field_name in data for field_name in quota_fields)

    def _quota_int(field_name: str, default: int, minimum: int, maximum: int) -> int:
        raw_value = data.get(field_name, default)
        if type(raw_value) is not int:
            errors.add(
                f"briefing.{field_name}",
                f"must be an integer between {minimum} and {maximum}, got {raw_value!r}",
            )
            return default
        value = raw_value
        if value < minimum or value > maximum:
            errors.add(
                f"briefing.{field_name}",
                f"must be between {minimum} and {maximum}, got {raw_value!r}",
            )
            # Keep a parseable out-of-range value long enough to report
            # cross-field problems (for example the total cap) in the same
            # validation pass. The config is never returned while errors exist.
            return value
        return value

    max_items = _quota_int("max_items", 5, 1, 10)
    quota_mode = mode == "signals" and not has_legacy_max
    if mode == "signals" and has_legacy_max and has_quota_fields:
        errors.add(
            "briefing.max_items",
            "cannot be combined with news_items, wechat_min_items, github_items or paper_items",
        )

    if quota_mode:
        news_items = _quota_int("news_items", 5, 1, 10)
        wechat_min_items = _quota_int("wechat_min_items", 2, 0, 10)
        github_items = _quota_int("github_items", 1, 0, 5)
        paper_items = _quota_int("paper_items", 1, 0, 5)
        if wechat_min_items > news_items:
            errors.add(
                "briefing.wechat_min_items",
                f"must not exceed briefing.news_items ({news_items}), got {wechat_min_items}",
            )
        total_items = news_items + github_items + paper_items
        if total_items > 20:
            errors.add(
                "briefing.total",
                f"news_items + github_items + paper_items must not exceed 20, got {total_items}",
            )
    elif mode == "signals":
        news_items = max_items
        wechat_min_items = 0
        github_items = 0
        paper_items = 0
    else:
        # Explicit legacy briefing modes ignore signal quota composition.
        news_items = 0
        wechat_min_items = 0
        github_items = 0
        paper_items = 0
    return BriefingConfig(
        enabled=bool(data.get("enabled", True)),
        mode=mode or "signals",
        keyword=keyword,
        # Use a length check, not `sources or default`. An empty
        # list is falsy under `or`, which made a config with only
        # invalid source entries silently fall back to the default
        # 3-source list — turning a validation error into a
        # different-file result the operator never asked for.
        sources=(
            sources
            if sources or sources_provided
            else (
                ["wechat", "hackernews", "x", "github", "papers"]
                if mode == "signals"
                else ["github", "papers", "wechat"]
            )
        ),
        since_days=since_days,
        freshness_hours=freshness_hours,
        max_items=max_items,
        news_items=news_items,
        wechat_min_items=wechat_min_items,
        github_items=github_items,
        paper_items=paper_items,
        quota_mode=quota_mode,
    )


def _parse_limits(raw: Any, errors: _ErrorBag) -> LimitsConfig:
    line, _ = _loc(raw)
    data = _as_mapping(raw, where="limits", errors=errors, line=line)

    def _positive_int(key: str, default: int) -> int:
        raw_value = data.get(key, default)
        key_line, _ = _loc(data.get(key))
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            errors.add(f"limits.{key}", f"must be a positive integer, got {raw_value!r}", line=key_line)
            return default
        if value <= 0:
            errors.add(f"limits.{key}", f"must be positive, got {value}", line=key_line)
            return default
        return value

    def _non_negative_int(key: str, default: int) -> int:
        raw_value = data.get(key, default)
        key_line, _ = _loc(data.get(key))
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            errors.add(f"limits.{key}", f"must be a non-negative integer, got {raw_value!r}", line=key_line)
            return default
        if value < 0:
            errors.add(f"limits.{key}", f"must be non-negative, got {value}", line=key_line)
            return default
        return value

    return LimitsConfig(
        max_github_search_calls=_positive_int("max_github_search_calls", 5),
        max_paper_categories=_positive_int("max_paper_categories", 5),
        skip_if_already_collected_hours=_non_negative_int("skip_if_already_collected_hours", 20),
        max_log_files=_non_negative_int("max_log_files", 30),
    )


def _has_source_work(config: DiscoveryConfig, source_name: str) -> bool:
    source = getattr(config.sources, source_name)
    if not source.enabled:
        return False
    if source_name == "github":
        return bool(source.repos or source.search)
    if source_name == "papers":
        return bool(source.categories)
    if source_name == "wechat":
        return bool(source.urls or source.accounts)
    if source_name == "hackernews":
        return bool(source.feeds)
    if source_name == "x":
        return bool(source.queries)
    return False


def _validate_signal_quota_sources(config: DiscoveryConfig, errors: _ErrorBag) -> None:
    briefing = config.briefing
    if not briefing.enabled or briefing.mode != "signals" or not briefing.quota_mode:
        return

    requirements = (
        ("github", briefing.github_items, "briefing.github_items"),
        ("papers", briefing.paper_items, "briefing.paper_items"),
        ("wechat", briefing.wechat_min_items, "briefing.wechat_min_items"),
    )
    for source_name, minimum, field_name in requirements:
        if minimum <= 0:
            continue
        if source_name not in briefing.sources:
            errors.add(
                field_name,
                f"requires {source_name!r} in briefing.sources",
            )
            continue
        source = getattr(config.sources, source_name)
        if not source.enabled:
            errors.add(field_name, f"requires sources.{source_name}.enabled: true")
        elif not _has_source_work(config, source_name):
            errors.add(
                field_name,
                f"requires at least one configured sources.{source_name} target",
            )

    if briefing.news_items > 0:
        viable_news = [
            source_name
            for source_name in ("wechat", "hackernews", "x")
            if source_name in briefing.sources and _has_source_work(config, source_name)
        ]
        if not viable_news:
            errors.add(
                "briefing.news_items",
                "requires at least one enabled realtime source with configured work inside briefing.sources",
            )


def load_config(path: Path | str) -> DiscoveryConfig:
    """Load and validate a discovery YAML configuration.

    Aggregates **all** validation problems before raising so users see every
    issue in a single run instead of fixing them one at a time.
    """
    config_path = Path(path)
    # Catch every "input is not a readable file" failure as one
    # operator-friendly error. ``Path.exists()`` is False for both
    # missing files and unreadable paths; ``read_text`` would otherwise
    # raise IsADirectoryError / PermissionError uncaught.
    if not config_path.is_file():
        raise DiscoveryConfigError(
            f"Config file not found or not a regular file: {config_path}"
        )

    try:
        raw = yaml.load(config_path.read_text(encoding="utf-8"), Loader=_LocatingLoader) or {}
    except yaml.YAMLError as exc:
        # yaml.YAMLError already carries line/column info; surface it.
        raise DiscoveryConfigError(f"Failed to parse YAML at {config_path}: {exc}") from exc
    except OSError as exc:
        # PermissionError / IsADirectoryError slipping through. We
        # already gated via is_file() but a TOCTOU race or a symlink
        # to a deleted target can still raise here.
        raise DiscoveryConfigError(
            f"Failed to read config at {config_path}: {exc}"
        ) from exc

    if not isinstance(raw, dict):
        raise DiscoveryConfigError(f"Top-level YAML must be a mapping, got {type(raw).__name__}")

    errors = _ErrorBag()

    sources_raw = raw.get("sources", {}) or {}
    sources_line, _ = _loc(sources_raw)
    sources_mapping = _as_mapping(sources_raw, where="sources", errors=errors, line=sources_line)

    config = DiscoveryConfig(
        output_root=_resolve_path(raw.get("output_root"), default=DEFAULT_OUTPUT_ROOT),
        log_dir=_resolve_path(raw.get("log_dir"), default=DEFAULT_LOG_DIR),
        sources=SourceConfig(
            github=_parse_github(sources_mapping.get("github"), errors),
            papers=_parse_papers(sources_mapping.get("papers"), errors),
            wechat=_parse_wechat(sources_mapping.get("wechat"), errors),
            hackernews=_parse_hackernews(sources_mapping.get("hackernews"), errors),
            x=_parse_x(sources_mapping.get("x"), errors),
        ),
        briefing=_parse_briefing(raw.get("briefing"), errors),
        limits=_parse_limits(raw.get("limits"), errors),
    )

    _validate_signal_quota_sources(config, errors)
    errors.raise_if_any()
    return config


EXAMPLE_CONFIG = """\
# AI Intel Station — daily discovery configuration
# Copy this file to `config/discovery.yaml` and edit to taste.
# `discovery.yaml` is git-ignored; this template is the source of truth.

output_root: output                  # relative to repo root; defaults to ./output
log_dir: .state/discovery            # per-run log files live here

sources:
  github:
    enabled: true
    repos:                            # explicit owner/repo to refresh each run
      - anthropics/claude-code
    search:                          # keyword searches via `gh search repos`
      - query: "agent harness"
        limit: 10
      - query: "llm evaluation framework"
        limit: 5

  papers:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL] # see collect/papers.py AI_CATEGORIES
    max_per_category: 10

  wechat:
    enabled: true                    # required by the default 2-item WeChat minimum
    urls: []                         # direct articles remain supported as signal inputs
    accounts:                        # public-index watchlist; no WeChat login required
      - name: 架构师
        wechat_id: JiaGouX
    index_limit: 10

  hackernews:
    enabled: true
    feeds: [newstories, showstories]
    keywords: [agent, llm, claude, openai]
    limit: 20

  x:
    enabled: false                   # requires a developer bearer token
    queries:
      - "(agent OR llm) lang:en -is:retweet"
    token_env: X_BEARER_TOKEN
    limit: 10

briefing:
  enabled: true
  mode: signals                      # legacy 'digest' and 'reading-list' remain available
  keyword: daily
  sources: [wechat, hackernews, x, github, papers]
  freshness_hours: 48                # verified publication time; maximum allowed is 72
  news_items: 5
  wechat_min_items: 2
  github_items: 1
  paper_items: 1
  since_days: 1                      # legacy modes only

limits:
  max_github_search_calls: 5
  max_paper_categories: 5
  skip_if_already_collected_hours: 20
  max_log_files: 30                 # keep at most 30 log files; 0 = unlimited
"""


def render_example_config() -> str:
    return EXAMPLE_CONFIG
