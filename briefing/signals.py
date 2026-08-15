from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping, Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from library.items import ResearchItem
from briefing.reports import _escape_link_text
from publish.obsidian import briefing_output_path, write_markdown


REALTIME_SOURCES = frozenset({"wechat", "hackernews", "x"})
EVIDENCE_SOURCES = frozenset({"github", "papers"})
TRACKING_QUERY_KEYS = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"})


def _single_line(value: object) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def _table_cell(value: object) -> str:
    return _single_line(value).replace("|", "\\|")


@dataclass
class SelectedSignal:
    title: str
    canonical_url: str | None
    published_at: str
    what: str
    why_now: str
    confidence: str
    signals: list[ResearchItem] = field(default_factory=list)
    evidence: list[ResearchItem] = field(default_factory=list)
    signal_source_count: int = 0
    watchlist: bool = False
    engagement_percentile: float = 0.5
    lane: str = "news"
    timestamp_field: str = "published_at"
    _published_datetime: datetime | None = field(default=None, repr=False)


@dataclass
class RenderedSignalBriefing:
    status: str
    markdown: str


@dataclass
class DailyBriefingSelection:
    papers: list[SelectedSignal] = field(default_factory=list)
    github: list[SelectedSignal] = field(default_factory=list)
    news: list[SelectedSignal] = field(default_factory=list)
    expected_news: int = 5
    expected_wechat: int = 2
    expected_github: int = 1
    expected_papers: int = 1
    quota_mode: bool = True

    @property
    def entries(self) -> list[SelectedSignal]:
        return [*self.papers, *self.github, *self.news]

    @property
    def actual_wechat(self) -> int:
        return sum(
            1
            for entry in self.news
            if any(signal.source == "wechat" for signal in entry.signals)
        )

    @property
    def missing(self) -> dict[str, int]:
        if not self.quota_mode:
            return {}
        missing: dict[str, int] = {}
        values = (
            ("papers", self.expected_papers, len(self.papers)),
            ("github", self.expected_github, len(self.github)),
            ("news", self.expected_news, len(self.news)),
            ("wechat", self.expected_wechat, self.actual_wechat),
        )
        for name, expected, actual in values:
            if actual < expected:
                missing[name] = expected - actual
        return missing

    @property
    def has_quota_shortfall(self) -> bool:
        return bool(self.missing)


def normalize_signal_url(value: str | None) -> str:
    if not value:
        return ""
    try:
        parts = urlsplit(value.strip())
    except ValueError:
        return value.strip()
    if not parts.scheme or not parts.netloc:
        return value.strip()
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_QUERY_KEYS
    ]
    path = parts.path.rstrip("/")
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            path,
            urlencode(sorted(query)),
            "",
        )
    )


def normalize_signal_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "").lower()
    without_punctuation = "".join(
        " " if unicodedata.category(char).startswith("P") else char
        for char in normalized
    )
    return " ".join(without_punctuation.split())


def _parse_source_datetime(value: str | None, *, source: str) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        parsed = None
    if parsed is None:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(
            tzinfo=ZoneInfo("Asia/Shanghai") if source == "wechat" else timezone.utc
        )
    return parsed.astimezone(timezone.utc)


def _role(item: ResearchItem) -> str:
    if item.signal_role in ("signal", "evidence"):
        return item.signal_role
    if item.source in EVIDENCE_SOURCES:
        return "evidence"
    if item.source in REALTIME_SOURCES:
        return "signal"
    return "evidence"


def _dedupe_keys(item: ResearchItem) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    normalized_url = normalize_signal_url(item.canonical_url)
    normalized_title = normalize_signal_title(item.title)
    if normalized_url:
        keys.add(("url", normalized_url))
    if normalized_title:
        keys.add(("title", normalized_title))
    return keys


def _group_signals(items: list[ResearchItem]) -> list[list[ResearchItem]]:
    groups: list[tuple[set[tuple[str, str]], list[ResearchItem]]] = []
    for item in sorted(
        items,
        key=lambda candidate: (
            candidate.source,
            normalize_signal_url(candidate.canonical_url),
            normalize_signal_title(candidate.title),
        ),
    ):
        keys = _dedupe_keys(item)
        matching = [index for index, (group_keys, _) in enumerate(groups) if keys & group_keys]
        if not matching:
            groups.append((set(keys), [item]))
            continue
        first = matching[0]
        groups[first][0].update(keys)
        groups[first][1].append(item)
        for index in reversed(matching[1:]):
            other_keys, other_items = groups.pop(index)
            groups[first][0].update(other_keys)
            groups[first][1].extend(other_items)
    return [group_items for _, group_items in groups]


def _engagement(item: ResearchItem) -> float:
    value = item.metadata.get("engagement_count", 0)
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return numeric if math.isfinite(numeric) and numeric >= 0 else 0.0


def _source_percentiles(items: list[ResearchItem]) -> dict[int, float]:
    by_source: dict[str, list[tuple[int, float]]] = {}
    for index, item in enumerate(items):
        by_source.setdefault(item.source, []).append((index, _engagement(item)))
    result: dict[int, float] = {}
    for candidates in by_source.values():
        if len(candidates) == 1:
            result[candidates[0][0]] = 0.5
            continue
        ordered_values = sorted(value for _, value in candidates)
        denominator = len(ordered_values) - 1
        for index, value in candidates:
            positions = [pos for pos, other in enumerate(ordered_values) if other == value]
            result[index] = (sum(positions) / len(positions)) / denominator
    return result


def _matches_group(item: ResearchItem, group: Sequence[ResearchItem]) -> bool:
    keys = _dedupe_keys(item)
    return any(keys & _dedupe_keys(signal) for signal in group)


def select_daily_signals(
    items: Sequence[ResearchItem],
    *,
    now: datetime | None = None,
    freshness_hours: int = 48,
    max_items: int = 5,
) -> list[SelectedSignal]:
    if freshness_hours <= 0 or freshness_hours > 72:
        raise ValueError("freshness_hours must be between 1 and 72")
    if max_items <= 0:
        raise ValueError("max_items must be positive")
    evaluation_time = now or datetime.now(timezone.utc)
    if evaluation_time.tzinfo is None:
        evaluation_time = evaluation_time.replace(tzinfo=timezone.utc)
    evaluation_time = evaluation_time.astimezone(timezone.utc)
    lower_bound = evaluation_time - timedelta(hours=freshness_hours)
    future_limit = evaluation_time + timedelta(minutes=5)

    fresh_signals: list[ResearchItem] = []
    published_by_identity: dict[int, datetime] = {}
    evidence = [item for item in items if _role(item) == "evidence"]
    for item in items:
        if _role(item) != "signal":
            continue
        published = _parse_source_datetime(item.published_at, source=item.source)
        if published is None or published < lower_bound or published > future_limit:
            continue
        fresh_signals.append(item)
        published_by_identity[id(item)] = published

    percentiles_by_index = _source_percentiles(fresh_signals)
    percentile_by_identity = {
        id(item): percentiles_by_index[index]
        for index, item in enumerate(fresh_signals)
    }

    selected: list[SelectedSignal] = []
    for group in _group_signals(fresh_signals):
        group = sorted(
            group,
            key=lambda item: (
                item.source,
                normalize_signal_url(item.canonical_url),
                item.title,
            ),
        )
        representative = group[0]
        group_evidence = sorted(
            [item for item in evidence if _matches_group(item, group)],
            key=lambda item: (item.source, normalize_signal_url(item.canonical_url), item.title),
        )
        newest = max(published_by_identity[id(item)] for item in group)
        watchlist = any(bool(item.metadata.get("watchlist")) for item in group)
        source_count = len({item.source for item in group})
        engagement_percentile = max(percentile_by_identity[id(item)] for item in group)
        if source_count >= 2 or (watchlist and group_evidence):
            confidence = "high"
        elif watchlist or group_evidence:
            confidence = "medium"
        else:
            confidence = "low"
        age_hours = max(0.0, (evaluation_time - newest).total_seconds() / 3600)
        age_band = "24h" if age_hours <= 24 else f"{freshness_hours}h"
        why_now = (
            f"age_band={age_band}; watchlist={'yes' if watchlist else 'no'}; "
            f"signal_sources={source_count}; evidence={len(group_evidence)}; "
            f"engagement_percentile={engagement_percentile:.2f}"
        )
        selected.append(
            SelectedSignal(
                title=representative.title,
                canonical_url=representative.canonical_url,
                published_at=newest.isoformat().replace("+00:00", "Z"),
                what=representative.summary or representative.title,
                why_now=why_now,
                confidence=confidence,
                signals=group,
                evidence=group_evidence,
                signal_source_count=source_count,
                watchlist=watchlist,
                engagement_percentile=engagement_percentile,
                _published_datetime=newest,
            )
        )

    selected.sort(
        key=lambda entry: (
            -(1 if (evaluation_time - (entry._published_datetime or evaluation_time)).total_seconds() <= 24 * 3600 else 0),
            -(1 if entry.watchlist else 0),
            -entry.signal_source_count,
            -entry.engagement_percentile,
            -(entry._published_datetime or datetime.min.replace(tzinfo=timezone.utc)).timestamp(),
            normalize_signal_url(entry.canonical_url),
            normalize_signal_title(entry.title),
        )
    )
    return selected[:max_items]


@dataclass
class _DedicatedCandidate:
    item: ResearchItem
    source_time: datetime
    timestamp_field: str
    created_inside_window: bool = False


def _fresh_dedicated_candidates(
    items: Sequence[ResearchItem],
    *,
    source: str,
    evaluation_time: datetime,
    lower_bound: datetime,
    future_limit: datetime,
) -> list[_DedicatedCandidate]:
    candidates: list[_DedicatedCandidate] = []
    for item in items:
        if item.source != source or _role(item) != "evidence":
            continue
        if source == "github":
            timestamp_field = "updated_at" if item.updated_at else "published_at"
            source_time = _parse_source_datetime(
                item.updated_at or item.published_at, source=source
            )
            created = _parse_source_datetime(item.published_at, source=source)
            created_inside = bool(
                created is not None and lower_bound <= created <= future_limit
            )
        else:
            timestamp_field = "published_at"
            source_time = _parse_source_datetime(item.published_at, source=source)
            created_inside = False
        if source_time is None or source_time < lower_bound or source_time > future_limit:
            continue
        candidates.append(
            _DedicatedCandidate(
                item=item,
                source_time=source_time,
                timestamp_field=timestamp_field,
                created_inside_window=created_inside,
            )
        )

    candidates.sort(
        key=lambda candidate: (
            -(1 if source == "github" and candidate.created_inside_window else 0),
            -candidate.source_time.timestamp(),
            normalize_signal_url(candidate.item.canonical_url),
            normalize_signal_title(candidate.item.title),
        )
    )
    unique: list[_DedicatedCandidate] = []
    seen_keys: set[tuple[str, str]] = set()
    for candidate in candidates:
        keys = _dedupe_keys(candidate.item)
        if keys & seen_keys:
            continue
        unique.append(candidate)
        seen_keys.update(keys)
    return unique


def _entry_keys(entry: SelectedSignal) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    normalized_url = normalize_signal_url(entry.canonical_url)
    normalized_title = normalize_signal_title(entry.title)
    if normalized_url:
        keys.add(("url", normalized_url))
    if normalized_title:
        keys.add(("title", normalized_title))
    return keys


def _dedicated_entry(
    candidate: _DedicatedCandidate,
    *,
    lane: str,
    news_entries: Sequence[SelectedSignal],
    evaluation_time: datetime,
    freshness_hours: int,
) -> SelectedSignal:
    candidate_keys = _dedupe_keys(candidate.item)
    matching_news = [entry for entry in news_entries if candidate_keys & _entry_keys(entry)]
    signals = sorted(
        [signal for entry in matching_news for signal in entry.signals],
        key=lambda item: (
            item.source,
            normalize_signal_url(item.canonical_url),
            normalize_signal_title(item.title),
        ),
    )
    source_count = len({item.source for item in signals})
    watchlist = any(
        item.source == "wechat" and bool(item.metadata.get("watchlist"))
        for item in signals
    )
    if source_count >= 2 or watchlist:
        confidence = "high"
    elif source_count == 1:
        confidence = "medium"
    else:
        confidence = "low"
    age_hours = max(
        0.0,
        (evaluation_time - candidate.source_time).total_seconds() / 3600,
    )
    age_band = "24h" if age_hours <= 24 else f"{freshness_hours}h"
    why_now = (
        f"lane={lane}; timestamp_field={candidate.timestamp_field}; age_band={age_band}; "
        f"signal_sources={source_count}; watchlist={'yes' if watchlist else 'no'}"
    )
    item = candidate.item
    return SelectedSignal(
        title=item.title,
        canonical_url=item.canonical_url,
        published_at=candidate.source_time.isoformat().replace("+00:00", "Z"),
        what=item.summary or item.title,
        why_now=why_now,
        confidence=confidence,
        signals=signals,
        evidence=[item],
        signal_source_count=source_count,
        watchlist=watchlist,
        lane=lane,
        timestamp_field=candidate.timestamp_field,
        _published_datetime=candidate.source_time,
    )


def select_daily_briefing(
    items: Sequence[ResearchItem],
    *,
    now: datetime | None = None,
    freshness_hours: int = 48,
    news_items: int = 5,
    wechat_min_items: int = 2,
    github_items: int = 1,
    paper_items: int = 1,
    quota_mode: bool = True,
) -> DailyBriefingSelection:
    """Compose deterministic News, GitHub and arXiv lanes.

    Stored item roles stay unchanged: realtime sources are selected into News,
    while fresh evidence can only seed its dedicated lane.
    """
    if freshness_hours <= 0 or freshness_hours > 72:
        raise ValueError("freshness_hours must be between 1 and 72")
    if news_items <= 0:
        raise ValueError("news_items must be positive")
    if min(wechat_min_items, github_items, paper_items) < 0:
        raise ValueError("lane quotas must be non-negative")
    if wechat_min_items > news_items:
        raise ValueError("wechat_min_items must not exceed news_items")

    evaluation_time = now or datetime.now(timezone.utc)
    if evaluation_time.tzinfo is None:
        evaluation_time = evaluation_time.replace(tzinfo=timezone.utc)
    evaluation_time = evaluation_time.astimezone(timezone.utc)
    lower_bound = evaluation_time - timedelta(hours=freshness_hours)
    future_limit = evaluation_time + timedelta(minutes=5)

    # Build the complete ranked News pool first so matching realtime signals
    # can corroborate a dedicated entry even when that News duplicate is not
    # rendered separately.
    news_pool = select_daily_signals(
        items,
        now=evaluation_time,
        freshness_hours=freshness_hours,
        max_items=max(1, len(items)),
    )
    paper_candidates = _fresh_dedicated_candidates(
        items,
        source="papers",
        evaluation_time=evaluation_time,
        lower_bound=lower_bound,
        future_limit=future_limit,
    )
    selected_paper_candidates = paper_candidates[:paper_items]
    paper_keys = {
        key
        for candidate in selected_paper_candidates
        for key in _dedupe_keys(candidate.item)
    }

    github_candidates = _fresh_dedicated_candidates(
        items,
        source="github",
        evaluation_time=evaluation_time,
        lower_bound=lower_bound,
        future_limit=future_limit,
    )
    selected_github_candidates: list[_DedicatedCandidate] = []
    github_keys: set[tuple[str, str]] = set()
    if github_items:
        for candidate in github_candidates:
            keys = _dedupe_keys(candidate.item)
            if keys & paper_keys:
                continue
            selected_github_candidates.append(candidate)
            github_keys.update(keys)
            if len(selected_github_candidates) >= github_items:
                break

    papers = [
        _dedicated_entry(
            candidate,
            lane="papers",
            news_entries=news_pool,
            evaluation_time=evaluation_time,
            freshness_hours=freshness_hours,
        )
        for candidate in selected_paper_candidates
    ]
    github = [
        _dedicated_entry(
            candidate,
            lane="github",
            news_entries=news_pool,
            evaluation_time=evaluation_time,
            freshness_hours=freshness_hours,
        )
        for candidate in selected_github_candidates
    ]

    dedicated_keys = paper_keys | github_keys
    available_news = [
        entry for entry in news_pool if not (_entry_keys(entry) & dedicated_keys)
    ]
    reserved_wechat = [
        entry
        for entry in available_news
        if any(signal.source == "wechat" for signal in entry.signals)
    ][:wechat_min_items]
    chosen_ids = {id(entry) for entry in reserved_wechat}
    for entry in available_news:
        if len(chosen_ids) >= news_items:
            break
        chosen_ids.add(id(entry))
    news = [entry for entry in available_news if id(entry) in chosen_ids][:news_items]
    for entry in news:
        entry.lane = "news"
        entry.timestamp_field = "published_at"

    return DailyBriefingSelection(
        papers=papers,
        github=github,
        news=news,
        expected_news=news_items,
        expected_wechat=wechat_min_items,
        expected_github=github_items,
        expected_papers=paper_items,
        quota_mode=quota_mode,
    )


def _source_status_lines(
    source_reports: Mapping[str, object],
    *,
    coverage_sources: Sequence[str] | None = None,
    required_sources: Sequence[str] = (),
    viable_news_sources: Sequence[str] = (),
) -> tuple[list[str], bool, list[str]]:
    lines = ["## Source Coverage", "", "| Source | Status | Succeeded | Skipped | Failed | Notes |", "|---|---:|---:|---:|---:|---|"]
    coverage_scope = set(coverage_sources) if coverage_sources is not None else None
    coverage_incomplete = False
    issues: list[str] = []
    for name, report in source_reports.items():
        enabled = bool(getattr(report, "enabled", False))
        succeeded = int(getattr(report, "succeeded", 0))
        skipped = int(getattr(report, "skipped", 0))
        failed = int(getattr(report, "failed", 0))
        notes = "; ".join(_table_cell(note) for note in getattr(report, "notes", []))
        status = "disabled" if not enabled else ("failed" if failed else "succeeded")
        failure_is_relevant = (
            name in coverage_scope if coverage_scope is not None else name in REALTIME_SOURCES
        )
        if enabled and failure_is_relevant and failed:
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
        f"### {index}. {title_link}",
        "",
        f"- 是什么：{_single_line(entry.what)}",
        f"- 为什么现在值得看：{entry.why_now}",
        f"- 来源时间（{entry.timestamp_field}）：{entry.published_at}",
        f"- Confidence：{entry.confidence}",
        "- Signals:",
    ]
    if entry.signals:
        for signal in entry.signals:
            link = f"[{signal.source}]({signal.canonical_url})" if signal.canonical_url else signal.source
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
) -> RenderedSignalBriefing:
    generated = now or datetime.now(timezone.utc)
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=timezone.utc)
    coverage_lines, coverage_incomplete, _ = _source_status_lines(
        source_reports,
        coverage_sources=coverage_sources,
        required_sources=required_sources,
        viable_news_sources=viable_news_sources,
    )
    selection = entries if isinstance(entries, DailyBriefingSelection) else None
    rendered_entries = selection.entries if selection is not None else list(entries)
    quota_shortfall = bool(selection and selection.has_quota_shortfall)
    if rendered_entries:
        status = "partial" if coverage_incomplete or quota_shortfall else "ready"
    else:
        status = "coverage_incomplete" if coverage_incomplete else "no_fresh_signals"

    lines = [
        f"# Daily Signals: {title}",
        "",
        f"> Status: {status}",
        f"> Generated: {generated.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        f"> Freshness: {freshness_hours}h",
        f"> Item count: {len(rendered_entries)}",
        "",
    ]
    lines.extend(coverage_lines)
    if selection is not None and selection.quota_mode:
        quota_rows = (
            ("arXiv", selection.expected_papers, len(selection.papers)),
            ("GitHub", selection.expected_github, len(selection.github)),
            ("News", selection.expected_news, len(selection.news)),
            ("WeChat minimum", selection.expected_wechat, selection.actual_wechat),
        )
        lines.extend(
            [
                "## Quota Coverage",
                "",
                "| Lane | Expected | Actual | Missing |",
                "|---|---:|---:|---:|",
            ]
        )
        for lane, expected, actual in quota_rows:
            lines.append(f"| {lane} | {expected} | {actual} | {max(0, expected - actual)} |")
        lines.append("")
    if not rendered_entries:
        if status == "coverage_incomplete":
            lines.extend(
                [
                    "## Result",
                    "",
                    "No verified fresh result can be concluded because realtime source coverage is incomplete.",
                    "",
                ]
            )
        else:
            lines.extend(["## Result", "", "No verified fresh signals were found.", ""])
        return RenderedSignalBriefing(status=status, markdown="\n".join(lines).rstrip() + "\n")

    if selection is None:
        lines.extend(["## Top Signals", ""])
        for index, entry in enumerate(rendered_entries, start=1):
            lines.extend(_entry_markdown(entry, index))
    else:
        next_index = 1
        for heading, lane_entries in (
            ("arXiv", selection.papers),
            ("GitHub", selection.github),
            ("News", selection.news),
        ):
            lines.extend([f"## {heading}", ""])
            if not lane_entries:
                lines.extend(["No verified fresh item for this lane.", ""])
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
) -> tuple[Path, str]:
    rendered = render_daily_signal_markdown(
        title,
        entries,
        source_reports,
        now=now,
        freshness_hours=freshness_hours,
        coverage_sources=coverage_sources,
        required_sources=required_sources,
        viable_news_sources=viable_news_sources,
    )
    path = briefing_output_path(output_root, "signals", title)
    write_markdown(path, rendered.markdown)
    return path, rendered.status
