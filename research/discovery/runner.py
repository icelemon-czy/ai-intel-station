from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from briefing.service import build_generic_briefing_from_items, save_generic_briefing
from briefing.signal_rendering import write_daily_signal_report
from briefing.signals import select_daily_briefing, select_daily_signals
from library.query import query_research_items
from library.storage import load_research_items

from .config import DiscoveryConfig
from .log import DiscoveryLogger
from .models import BriefingArtifact, DiscoveryReport, SourceReport
from .sources import (
    collect_github,
    collect_hackernews,
    collect_papers,
    collect_wechat,
    collect_x,
)


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _format_since(days: int) -> str:
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


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

    generic = build_generic_briefing_from_items(
        mode=briefing.mode,
        title=title,
        items=items,
        requested_sources=briefing.sources,
    )
    saved = save_generic_briefing(generic, config.output_root)
    assert saved.path is not None
    path = saved.path

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
