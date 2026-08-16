from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from collect.github import (
    save_repo as github_save_repo,
    save_search_results as github_save_search_results,
)
import collect.github as github_module
from collect.papers import AI_CATEGORIES
import collect.papers as papers_module
import collect.wechat as wechat_module
import collect.hackernews as hackernews_module
import collect.wechat_index as wechat_index_module
import collect.x as x_module
import briefing.reports as briefing_reports
from briefing.signals import (
    select_daily_briefing,
    select_daily_signals,
    write_daily_signal_report,
)
from library.query import query_research_items
from library.storage import load_research_items

from .config import DiscoveryConfig, GitHubSearchQuery
from .log import DiscoveryLogger


@dataclass
class SourceReport:
    name: str
    enabled: bool = False
    skipped: int = 0
    succeeded: int = 0
    failed: int = 0
    output_paths: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class BriefingArtifact:
    path: Path | None
    mode: str
    item_count: int
    status: str


@dataclass
class DiscoveryReport:
    started_at: str
    finished_at: str
    dry_run: bool
    log_path: Path | None
    sources: dict[str, SourceReport] = field(default_factory=dict)
    briefing: BriefingArtifact | None = None

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "log_path": self.log_path.as_posix() if self.log_path else None,
            "sources": {
                name: {
                    "enabled": report.enabled,
                    "skipped": report.skipped,
                    "succeeded": report.succeeded,
                    "failed": report.failed,
                    "notes": report.notes,
                    "output_paths": [path.as_posix() for path in report.output_paths],
                }
                for name, report in self.sources.items()
            },
            "briefing": (
                {
                    "path": self.briefing.path.as_posix() if self.briefing.path else None,
                    "mode": self.briefing.mode,
                    "item_count": self.briefing.item_count,
                    "status": self.briefing.status,
                }
                if self.briefing
                else None
            ),
        }


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _format_since(days: int) -> str:
    moment = datetime.now() - timedelta(days=days)
    return moment.strftime("%Y-%m-%d")


def _recent_enough(path: Path, threshold_hours: int) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age.total_seconds() < threshold_hours * 3600


def _github_search_repos(query: str, limit: int, logger: DiscoveryLogger | None) -> list[dict]:
    payload = github_module.run_gh(
        [
            "search",
            "repos",
            query,
            "--sort",
            "updated",
            "--limit",
            str(limit),
            "--json",
            "name,owner,description,url,stargazersCount,createdAt,updatedAt",
        ]
    )
    return json.loads(payload)


def collect_github(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    github = config.sources.github
    report = SourceReport(name="github", enabled=github.enabled)

    if not github.enabled:
        report.notes.append("disabled in config")
        return report

    github_root = config.output_root / "github"
    search_calls = min(len(github.search), config.limits.max_github_search_calls)

    if dry_run:
        for repo in github.repos:
            report.notes.append(f"[dry-run] would refresh repo {repo}")
            report.succeeded += 1
        for query in github.search[:search_calls]:
            report.notes.append(f"[dry-run] would search '{query.query}' (limit={query.limit})")
            report.succeeded += 1
        if len(github.search) > search_calls:
            report.notes.append(
                f"[dry-run] skipped {len(github.search) - search_calls} search calls (limits.max_github_search_calls={search_calls})"
            )
            report.skipped += len(github.search) - search_calls
        return report

    github_root.mkdir(parents=True, exist_ok=True)
    skip_threshold = config.limits.skip_if_already_collected_hours

    for target in github.repos:
        if "/" not in target:
            report.notes.append(f"skip invalid repo target {target!r}")
            report.failed += 1
            continue
        owner, repo = target.split("/", 1)
        existing = github_root / f"{owner}-{repo}"
        if _recent_enough(existing, skip_threshold):
            report.notes.append(f"skip {owner}/{repo} (collected within last {skip_threshold}h)")
            report.skipped += 1
            continue
        try:
            if logger:
                logger.log(f"📦 Fetching GitHub repo {owner}/{repo}...")
            result_path = github_module.save_repo(owner, repo, github_root)
            report.output_paths.append(result_path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{owner}/{repo} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {owner}/{repo}: {exc}")

    for query in github.search[:search_calls]:
        if logger:
            logger.log(f"🔍 GitHub search: '{query.query}' (limit={query.limit})")
        try:
            repos = _github_search_repos(query.query, query.limit, logger)
            result_path = github_module.save_search_results(query.query, github_root, repos)
            report.output_paths.append(result_path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"search '{query.query}' failed: {exc}")
            if logger:
                logger.log(f"  ❌ search '{query.query}': {exc}")

    if len(github.search) > search_calls:
        skipped = len(github.search) - search_calls
        report.skipped += skipped
        report.notes.append(
            f"skipped {skipped} search calls (limits.max_github_search_calls={search_calls})"
        )

    return report


def collect_hackernews(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    source = config.sources.hackernews
    report = SourceReport(name="hackernews", enabled=source.enabled)
    if not source.enabled:
        report.notes.append("disabled in config")
        return report
    if not source.feeds:
        report.failed = 1
        report.notes.append("no Hacker News feeds configured; realtime coverage is incomplete")
        return report
    if dry_run:
        for feed in source.feeds:
            report.succeeded += 1
            report.notes.append(
                f"[dry-run] would scan Hacker News {feed} (limit={source.limit}, keywords={source.keywords})"
            )
        return report

    output_root = config.output_root / "hackernews"
    for feed in source.feeds:
        try:
            if logger:
                logger.log(f"📰 Fetching Hacker News {feed}...")
            path = hackernews_module.collect_feed(
                feed,
                keywords=source.keywords,
                limit=source.limit,
                output_dir=output_root,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{feed} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {feed}: {exc}")
    return report


def collect_x(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    source = config.sources.x
    report = SourceReport(name="x", enabled=source.enabled)
    if not source.enabled:
        report.notes.append("disabled in config")
        return report
    if not source.queries:
        report.failed = 1
        report.notes.append("no X queries configured; realtime coverage is incomplete")
        return report
    if dry_run:
        for query in source.queries:
            report.succeeded += 1
            report.notes.append(
                f"[dry-run] would run X recent search {query!r} "
                f"(limit={source.limit}, freshness={config.briefing.freshness_hours}h, "
                f"token_env={source.token_env})"
            )
        return report

    output_root = config.output_root / "x"
    for query in source.queries:
        try:
            if logger:
                logger.log(f"𝕏 Recent search: {query!r}")
            path = x_module.collect_recent_search(
                query,
                token_env=source.token_env,
                limit=source.limit,
                output_dir=output_root,
                freshness_hours=config.briefing.freshness_hours,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{query!r} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {query!r}: {exc}")
    return report


def collect_papers(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    papers = config.sources.papers
    report = SourceReport(name="papers", enabled=papers.enabled)

    if not papers.enabled:
        report.notes.append("disabled in config")
        return report

    if not papers.categories:
        report.notes.append("no categories configured")
        return report

    categories = list(papers.categories)
    if len(categories) > config.limits.max_paper_categories:
        skipped = len(categories) - config.limits.max_paper_categories
        report.skipped += skipped
        report.notes.append(
            f"truncated {skipped} categories (limits.max_paper_categories={config.limits.max_paper_categories})"
        )
        categories = categories[: config.limits.max_paper_categories]

    if dry_run:
        for category in categories:
            report.notes.append(
                f"[dry-run] would fetch up to {papers.max_per_category} papers for {category} ({AI_CATEGORIES.get(category, '?')})"
            )
            report.succeeded += 1
        return report

    papers_root = config.output_root / "papers"
    papers_root.mkdir(parents=True, exist_ok=True)

    for category in categories:
        if logger:
            logger.log(f"📚 Fetching arXiv {category} ({AI_CATEGORIES.get(category, '?')})...")
        try:
            fetched = papers_module.fetch_papers_by_category(
                [category],
                papers.max_per_category,
                raise_on_error=True,
            )
            if not fetched:
                report.notes.append(f"{category}: no papers returned")
                continue
            papers_module.save_papers(fetched, category, papers_root)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{category} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {category}: {exc}")

    return report


def collect_wechat(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    wechat = config.sources.wechat
    report = SourceReport(name="wechat", enabled=wechat.enabled)

    if not wechat.enabled:
        report.notes.append("disabled in config (default)")
        return report

    if not wechat.urls and not wechat.accounts:
        report.failed = 1
        report.notes.append("no WeChat URLs or accounts configured; realtime coverage is incomplete")
        return report

    if dry_run:
        for url in wechat.urls:
            report.notes.append(f"[dry-run] would fetch WeChat article {url}")
            report.succeeded += 1
        for account in wechat.accounts:
            report.notes.append(
                f"[dry-run] would query public WeChat index for {account.name} ({account.wechat_id})"
            )
            report.succeeded += 1
        return report

    wechat_root = config.output_root / "wechat"
    wechat_root.mkdir(parents=True, exist_ok=True)
    skip_threshold = config.limits.skip_if_already_collected_hours

    for url in wechat.urls:
        target = wechat_root / url.rsplit("/", 1)[-1].split("?")[0]
        # dedup by raw URL substring presence in any sidecar
        if any(url in str(path.read_text(errors="ignore")) for path in wechat_root.rglob("research-item.json") if path.exists()):
            if _recent_enough(target, skip_threshold) or any(_recent_enough(path, skip_threshold) for path in wechat_root.iterdir() if path.is_dir()):
                report.notes.append(f"skip {url} (recently collected)")
                report.skipped += 1
                continue
        try:
            if logger:
                logger.log(f"🦊 Fetching WeChat article: {url}")
            path = asyncio.run(wechat_module.fetch_article(url, output_dir=wechat_root))
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{url} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {url}: {exc}")

    for account in wechat.accounts:
        try:
            if logger:
                logger.log(
                    f"🔎 WeChat public index: {account.name} ({account.wechat_id})"
                )
            path = wechat_index_module.collect_account(
                account.name,
                account.wechat_id,
                limit=wechat.index_limit,
                output_dir=wechat_root,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{account.name} index failed: {exc}")
            if logger:
                logger.log(f"  ❌ {account.name}: {exc}")

    return report


def generate_briefing(
    config: DiscoveryConfig,
    report_log: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
    source_reports: dict[str, SourceReport] | None = None,
    now: datetime | None = None,
) -> BriefingArtifact | None:
    briefing = config.briefing
    if not briefing.enabled:
        if report_log:
            report_log.log("🗂  Briefing disabled — skipping.")
        return None

    if dry_run:
        if report_log:
            composition = (
                f"composition={briefing.hackernews_items} Hacker News + "
                f"WeChat optional maximum={briefing.wechat_max_items} "
                f"(minimum={briefing.wechat_min_items}) + "
                f"{briefing.x_items} X + "
                f"{briefing.github_items} GitHub + {briefing.paper_items} arXiv"
                if briefing.mode == "signals" and briefing.quota_mode
                else f"max_items={briefing.max_items}"
            )
            report_log.log(
                f"[dry-run] would generate {briefing.mode} briefing '{briefing.keyword}' "
                f"from sources={briefing.sources} window={briefing.since_days}d {composition}"
            )
        return BriefingArtifact(
            path=Path("(dry-run)"), mode=briefing.mode, item_count=0, status="dry_run"
        )

    title_date = (now or datetime.now(timezone.utc)).astimezone().strftime("%Y-%m-%d")
    title = f"{briefing.keyword}-{title_date}"
    if briefing.mode == "signals":
        items = [
            item
            for item in load_research_items(config.output_root)
            if item.source in briefing.sources
        ]
        if briefing.quota_mode:
            entries = select_daily_briefing(
                items,
                now=now,
                freshness_hours=briefing.freshness_hours,
                hackernews_items=briefing.hackernews_items,
                wechat_min_items=briefing.wechat_min_items,
                wechat_max_items=briefing.wechat_max_items,
                x_items=briefing.x_items,
                github_items=briefing.github_items,
                paper_items=briefing.paper_items,
                quota_mode=True,
            )
            required_sources = [
                source_name
                for source_name, minimum in (
                    ("github", briefing.github_items),
                    ("papers", briefing.paper_items),
                    ("wechat", briefing.wechat_min_items),
                    ("hackernews", briefing.hackernews_items),
                    ("x", briefing.x_items),
                )
                if minimum > 0
            ]
            viable_news_sources = [
                source_name
                for source_name in ("wechat", "hackernews", "x")
                if source_name in briefing.sources
                and getattr(config.sources, source_name).enabled
                and (
                    bool(config.sources.wechat.urls or config.sources.wechat.accounts)
                    if source_name == "wechat"
                    else bool(config.sources.hackernews.feeds)
                    if source_name == "hackernews"
                    else bool(config.sources.x.queries)
                )
            ]
            render_options = {
                # A source selected by this actual sweep remains relevant to
                # coverage even when it is not used as a briefing item input.
                # Its failure must never coexist with a `ready` artifact.
                "coverage_sources": list(
                    dict.fromkeys(
                        [*briefing.sources, *(source_reports or {}).keys()]
                    )
                ),
                "required_sources": required_sources,
                "viable_news_sources": viable_news_sources,
                "optional_sources": (
                    ["wechat"]
                    if briefing.wechat_min_items == 0
                    and briefing.wechat_max_items > 0
                    else []
                ),
            }
            item_count = len(entries.entries)
        else:
            entries = select_daily_signals(
                items,
                now=now,
                freshness_hours=briefing.freshness_hours,
                max_items=briefing.max_items,
            )
            render_options = {}
            item_count = len(entries)
        path, status = write_daily_signal_report(
            config.output_root,
            title=title,
            entries=entries,
            source_reports=source_reports or {},
            now=now,
            freshness_hours=briefing.freshness_hours,
            **render_options,
        )
        if report_log:
            report_log.log(
                f"📰 Signal briefing saved: {path} ({item_count} items, status={status})"
            )
        return BriefingArtifact(
            path=path,
            mode="signals",
            item_count=item_count,
            status=status,
        )

    since = _format_since(briefing.since_days)
    items = query_research_items(
        config.output_root,
        keyword=None,
        sources=briefing.sources,
        since=since,
        until=None,
    )

    if briefing.mode == "digest":
        path = briefing_reports.write_digest_report(
            config.output_root, title=title, items=items, requested_sources=briefing.sources
        )
    else:
        path = briefing_reports.write_reading_list_report(
            config.output_root, title=title, items=items, requested_sources=briefing.sources
        )

    if report_log:
        report_log.log(f"📰 Briefing saved: {path} ({len(items)} items)")
    return BriefingArtifact(
        path=path, mode=briefing.mode, item_count=len(items), status="legacy"
    )


def run_discovery(
    config: DiscoveryConfig,
    *,
    only: list[str] | None = None,
    dry_run: bool = False,
    log_dir: Path | None = None,
    enable_briefing: bool = True,
) -> DiscoveryReport:
    """Run a full discovery sweep driven by ``config``.

    Parameters
    ----------
    config:
        Validated :class:`DiscoveryConfig` instance.
    only:
        Optional list of source names (``github`` / ``papers`` / ``wechat`` /
        ``hackernews`` / ``x``) to limit the
        sweep to. Useful for ``research discover --source papers``.
    dry_run:
        When ``True``, do not hit the network; just report what would have been done.
    log_dir:
        Override the log directory (defaults to ``config.log_dir``).
    enable_briefing:
        When ``False``, skip the briefing step even if the YAML enables it.
    """
    started_at = _now_iso()
    log_path: Path | None = None
    logger = DiscoveryLogger(log_dir or config.log_dir, max_log_files=config.limits.max_log_files)
    log_path = logger.path
    try:
        logger.header(f"discovery sweep (dry_run={dry_run})")
        if only:
            logger.log(f"Limiting sweep to sources: {', '.join(only)}")

        selected_sources = {
            "github": collect_github,
            "papers": collect_papers,
            "wechat": collect_wechat,
            "hackernews": collect_hackernews,
            "x": collect_x,
        }

        source_reports: dict[str, SourceReport] = {}
        for name, runner in selected_sources.items():
            if only and name not in only:
                continue
            logger.header(f"source: {name}")
            try:
                source_reports[name] = runner(config, logger=logger, dry_run=dry_run)
            except Exception as exc:
                logger.log(f"❌ {name} crashed: {exc}")
                source_reports[name] = SourceReport(name=name, enabled=True, failed=1, notes=[str(exc)])
            report = source_reports[name]
            logger.log(
                f"  ↳ {name}: succeeded={report.succeeded} skipped={report.skipped} failed={report.failed}"
            )

        briefing_artifact: BriefingArtifact | None = None
        if enable_briefing:
            logger.header("briefing")
            try:
                briefing_artifact = generate_briefing(
                    config,
                    logger,
                    dry_run=dry_run,
                    source_reports=source_reports,
                )
            except Exception as exc:
                logger.log(f"❌ briefing crashed: {exc}")
                briefing_artifact = BriefingArtifact(
                    path=None,
                    mode=config.briefing.mode,
                    item_count=0,
                    status="failed",
                )
        else:
            logger.log("🗂  Briefing skipped (--no-briefing).")

        report = DiscoveryReport(
            started_at=started_at,
            finished_at=_now_iso(),
            dry_run=dry_run,
            log_path=log_path,
            sources=source_reports,
            briefing=briefing_artifact,
        )

        # Compact summary: friendly for humans, machine-readable for tooling.
        total_succeeded = sum(r.succeeded for r in source_reports.values())
        total_failed = sum(r.failed for r in source_reports.values())
        total_skipped = sum(r.skipped for r in source_reports.values())
        logger.log("")
        logger.log(
            f"📊 Summary: succeeded={total_succeeded} skipped={total_skipped} failed={total_failed}"
        )
        if briefing_artifact:
            logger.log(
                f"📰 Briefing: {briefing_artifact.path} "
                f"({briefing_artifact.item_count} items, status={briefing_artifact.status})"
            )
        if total_failed:
            logger.log(f"⚠️  See log for failure details: {log_path}")

        logger.log("")
        logger.log(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return report
    finally:
        # Always close the log handle — otherwise a crash between the
        # DiscoveryLogger constructor and the explicit close() below
        # would leak the file descriptor for the rest of the process.
        logger.close()
