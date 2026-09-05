from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping, Sequence

from ai_intel_station.briefing.reports import _escape_link_text
from ai_intel_station.briefing.markdown import briefing_output_path, write_markdown

from .signal_models import DailyBriefingSelection, REALTIME_SOURCES, RenderedSignalBriefing, SelectedSignal


def _single_line(value: object) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def _table_cell(value: object) -> str:
    return _single_line(value).replace("|", "\\|")


def _source_status_lines(
    source_reports: Mapping[str, object],
    *,
    coverage_sources: Sequence[str] | None = None,
    required_sources: Sequence[str] = (),
    viable_news_sources: Sequence[str] = (),
    optional_sources: Sequence[str] = (),
) -> tuple[list[str], bool, list[str]]:
    lines = ["## Source Coverage", "", "| Source | Status | Succeeded | Skipped | Failed | Notes |", "|---|---:|---:|---:|---:|---|"]
    coverage_scope = set(coverage_sources) if coverage_sources is not None else None
    coverage_incomplete = False
    issues: list[str] = []
    optional = set(optional_sources)
    completed_news_sources = {
        name
        for name, report in source_reports.items()
        if name in viable_news_sources
        and bool(getattr(report, "enabled", False))
        and int(getattr(report, "failed", 0)) == 0
    }
    for name, report in source_reports.items():
        enabled = bool(getattr(report, "enabled", False))
        succeeded = int(getattr(report, "succeeded", 0))
        skipped = int(getattr(report, "skipped", 0))
        failed = int(getattr(report, "failed", 0))
        notes = "; ".join(_table_cell(note) for note in getattr(report, "notes", []))
        ignored_optional_failure = bool(
            enabled and failed and name in optional and (completed_news_sources - {name})
        )
        status = (
            "disabled"
            if not enabled
            else "optional-failed"
            if ignored_optional_failure
            else "failed"
            if failed
            else "succeeded"
        )
        failure_is_relevant = name in coverage_scope if coverage_scope is not None else name in REALTIME_SOURCES
        if enabled and failure_is_relevant and failed and not ignored_optional_failure:
            coverage_incomplete = True
            issues.append(f"attempted source failed: {name}")
        lines.append(f"| {name} | {status} | {succeeded} | {skipped} | {failed} | {notes} |")
    lines.append("")
    attempted = set(source_reports)
    for source_name in required_sources:
        if source_name not in attempted:
            coverage_incomplete = True
            issues.append(f"unattempted required source: {source_name}")
    if viable_news_sources and not (attempted & set(viable_news_sources)):
        coverage_incomplete = True
        issues.append("unattempted News coverage")
    if issues:
        lines.extend(["Coverage issues: " + "; ".join(issues), ""])
    return lines, coverage_incomplete, issues


def _entry_markdown(entry: SelectedSignal, index: int) -> list[str]:
    safe_title = _escape_link_text(entry.title)
    title_link = f"[{safe_title}]({entry.canonical_url})" if entry.canonical_url else safe_title
    lines = [
        f"### {index}. {title_link}", "",
        f"- 是什么：{_single_line(entry.what)}",
        f"- 为什么现在值得看：{entry.why_now}",
        f"- 来源时间（{entry.timestamp_field}）：{entry.published_at}",
        f"- Confidence：{entry.confidence}",
        "- Signals:",
    ]
    if entry.signals:
        for signal in entry.signals:
            attribution_url = signal.canonical_url
            if signal.source == "hackernews":
                discussion_url = signal.metadata.get("discussion_url")
                if isinstance(discussion_url, str) and discussion_url.strip():
                    attribution_url = discussion_url.strip()
            link = f"[{signal.source}]({attribution_url})" if attribution_url else signal.source
            lines.append(f"  - {link} — {_single_line(signal.title)}")
    else:
        lines.append("  - none")
    lines.append("- Evidence:")
    if entry.evidence:
        for item in entry.evidence:
            link = f"[{item.source}]({item.canonical_url})" if item.canonical_url else item.source
            lines.append(f"  - {link} — {_single_line(item.title)}")
    else:
        lines.append("  - none")
    lines.append("")
    return lines


def render_daily_signal_markdown(
    title: str,
    entries: Sequence[SelectedSignal] | DailyBriefingSelection,
    source_reports: Mapping[str, object],
    *,
    now: datetime | None = None,
    freshness_hours: int = 48,
    coverage_sources: Sequence[str] | None = None,
    required_sources: Sequence[str] = (),
    viable_news_sources: Sequence[str] = (),
    optional_sources: Sequence[str] = (),
) -> RenderedSignalBriefing:
    generated = now or datetime.now(timezone.utc)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    coverage_lines, coverage_incomplete, _ = _source_status_lines(
        source_reports,
        coverage_sources=coverage_sources,
        required_sources=required_sources,
        viable_news_sources=viable_news_sources,
        optional_sources=optional_sources,
    )
    selection = entries if isinstance(entries, DailyBriefingSelection) else None
    rendered_entries = selection.entries if selection is not None else list(entries)
    quota_shortfall = bool(selection and selection.has_quota_shortfall)
    status = (
        "partial" if rendered_entries and (coverage_incomplete or quota_shortfall)
        else "ready" if rendered_entries
        else "coverage_incomplete" if coverage_incomplete
        else "no_fresh_signals"
    )
    lines = [
        f"# Daily Signals: {title}", "",
        f"> Status: {status}",
        f"> Generated: {generated.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"> Freshness: {freshness_hours}h",
        f"> Item count: {len(rendered_entries)}", "",
    ]
    lines.extend(coverage_lines)
    if selection is not None and selection.quota_mode:
        quota_rows = [
            ("arXiv", selection.expected_papers, len(selection.papers)),
            ("GitHub", selection.expected_github, len(selection.github)),
            ("Hacker News", selection.expected_hackernews, len(selection.hackernews)),
        ]
        if selection.expected_wechat > 0:
            quota_rows.append(("WeChat minimum", selection.expected_wechat, selection.actual_wechat))
        if selection.expected_x > 0:
            quota_rows.append(("X", selection.expected_x, len(selection.x)))
        lines.extend(["## Quota Coverage", "", "| Source | Expected | Actual | Missing |", "|---|---:|---:|---:|"])
        for source_name, expected, actual in quota_rows:
            lines.append(f"| {source_name} | {expected} | {actual} | {max(0, expected - actual)} |")
        lines.append("")
        if selection.max_wechat > 0 or selection.expected_wechat > 0:
            lines.extend([f"WeChat optional maximum: {selection.actual_wechat}/{selection.max_wechat}", ""])
    if not rendered_entries:
        result = (
            "No verified fresh result can be concluded because realtime source coverage is incomplete."
            if status == "coverage_incomplete"
            else "No verified fresh signals were found."
        )
        lines.extend(["## Result", "", result, ""])
        return RenderedSignalBriefing(status=status, markdown="\n".join(lines).rstrip() + "\n")
    if selection is None:
        lines.extend(["## Top Signals", ""])
        for index, entry in enumerate(rendered_entries, start=1):
            lines.extend(_entry_markdown(entry, index))
    else:
        next_index = 1
        source_sections = [
            ("arXiv", selection.papers, selection.expected_papers > 0),
            ("GitHub", selection.github, selection.expected_github > 0),
            ("Hacker News", selection.hackernews, selection.expected_hackernews > 0),
            ("WeChat", selection.wechat, selection.max_wechat > 0 or selection.expected_wechat > 0),
            ("X", selection.x, selection.expected_x > 0),
        ]
        for heading, lane_entries, include in source_sections:
            if not include and not lane_entries:
                continue
            lines.extend([f"## {heading}", ""])
            if not lane_entries:
                lines.extend(["No verified fresh item for this source.", ""])
                continue
            for entry in lane_entries:
                lines.extend(_entry_markdown(entry, next_index))
                next_index += 1
    return RenderedSignalBriefing(status=status, markdown="\n".join(lines).rstrip() + "\n")


def write_daily_signal_report(
    output_root: Path,
    *,
    title: str,
    entries: Sequence[SelectedSignal] | DailyBriefingSelection,
    source_reports: Mapping[str, object],
    now: datetime | None = None,
    freshness_hours: int = 48,
    coverage_sources: Sequence[str] | None = None,
    required_sources: Sequence[str] = (),
    viable_news_sources: Sequence[str] = (),
    optional_sources: Sequence[str] = (),
) -> tuple[Path, str]:
    rendered = render_daily_signal_markdown(
        title, entries, source_reports, now=now, freshness_hours=freshness_hours,
        coverage_sources=coverage_sources, required_sources=required_sources,
        viable_news_sources=viable_news_sources, optional_sources=optional_sources,
    )
    path = briefing_output_path(output_root, "signals", title)
    write_markdown(path, rendered.markdown)
    return path, rendered.status
