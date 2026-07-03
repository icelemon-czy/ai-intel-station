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
from collect.wechat import fetch_article as wechat_fetch_article
import collect.wechat as wechat_module
import briefing.reports as briefing_reports
from library.query import query_research_items

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
    path: Path
    mode: str
    item_count: int


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
                    "path": self.briefing.path.as_posix(),
                    "mode": self.briefing.mode,
                    "item_count": self.briefing.item_count,
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
            "stars",
            "--limit",
            str(limit),
            "--json",
            "name,owner,description,url,stargazersCount",
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
            github_module.save_repo(owner, repo, github_root)
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
            fetched = papers_module.fetch_papers_by_category([category], papers.max_per_category)
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

    if not wechat.urls:
        report.notes.append("no urls configured")
        return report

    if dry_run:
        for url in wechat.urls:
            report.notes.append(f"[dry-run] would fetch WeChat article {url}")
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
            asyncio.run(wechat_module.fetch_article(url, output_dir=wechat_root))
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{url} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {url}: {exc}")

    return report


def generate_briefing(
    config: DiscoveryConfig,
    report_log: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> BriefingArtifact | None:
    briefing = config.briefing
    if not briefing.enabled:
        if report_log:
            report_log.log("🗂  Briefing disabled — skipping.")
        return None

    if dry_run:
        if report_log:
            report_log.log(
                f"[dry-run] would generate {briefing.mode} briefing '{briefing.keyword}' "
                f"from sources={briefing.sources} window={briefing.since_days}d"
            )
        return BriefingArtifact(path=Path("(dry-run)"), mode=briefing.mode, item_count=0)

    since = _format_since(briefing.since_days)
    items = query_research_items(
        config.output_root,
        keyword=None,
        sources=briefing.sources,
        since=since,
        until=None,
    )

    title = f"{briefing.keyword}-{datetime.now().strftime('%Y-%m-%d')}"
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
    return BriefingArtifact(path=path, mode=briefing.mode, item_count=len(items))


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
        Optional list of source names (``github`` / ``papers`` / ``wechat``) to limit the
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
                briefing_artifact = generate_briefing(config, logger, dry_run=dry_run)
            except Exception as exc:
                logger.log(f"❌ briefing crashed: {exc}")
                briefing_artifact = None
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
            logger.log(f"📰 Briefing: {briefing_artifact.path} ({briefing_artifact.item_count} items)")
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