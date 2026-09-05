from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "discovery.yaml"
EXAMPLE_CONFIG_PATH = Path(__file__).with_name("discovery.yaml.example")
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
    # configs use the explicit source quota fields below.
    max_items: int = 5
    hackernews_items: int = 3
    wechat_min_items: int = 0
    wechat_max_items: int = 2
    x_items: int = 0
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


def _resolve_path(value: Any, *, default: Path) -> Path:
    if value is None or value == "":
        return Path(default)
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path
