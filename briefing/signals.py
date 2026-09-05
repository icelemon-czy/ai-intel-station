from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from library.items import ResearchItem

from .signal_models import (
    DailyBriefingSelection,
    EVIDENCE_SOURCES,
    REALTIME_SOURCES,
    SelectedSignal,
    TRACKING_QUERY_KEYS,
)

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
        f"source={lane}; timestamp_field={candidate.timestamp_field}; age_band={age_band}; "
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


def _primary_realtime_source(entry: SelectedSignal) -> str | None:
    for source in ("hackernews", "wechat", "x"):
        if any(signal.source == source for signal in entry.signals):
            return source
    return None


def _take_source_entries(
    available: Sequence[SelectedSignal],
    *,
    source: str,
    limit: int,
) -> list[SelectedSignal]:
    if limit <= 0:
        return []
    chosen: list[SelectedSignal] = []
    for entry in available:
        if _primary_realtime_source(entry) != source:
            continue
        chosen.append(entry)
        if len(chosen) >= limit:
            break
    return chosen


def select_daily_briefing(
    items: Sequence[ResearchItem],
    *,
    now: datetime | None = None,
    freshness_hours: int = 48,
    hackernews_items: int = 3,
    wechat_min_items: int = 0,
    wechat_max_items: int | None = None,
    x_items: int = 0,
    github_items: int = 1,
    paper_items: int = 1,
    quota_mode: bool = True,
) -> DailyBriefingSelection:
    """Compose deterministic source sections.

    Stored item roles stay unchanged: realtime sources fill their own
    sections, while fresh evidence can only seed github/papers.
    """
    if freshness_hours <= 0 or freshness_hours > 72:
        raise ValueError("freshness_hours must be between 1 and 72")
    if min(hackernews_items, wechat_min_items, x_items, github_items, paper_items) < 0:
        raise ValueError("source quotas must be non-negative")
    resolved_wechat_max = 2 if wechat_max_items is None else wechat_max_items
    if resolved_wechat_max < 0:
        raise ValueError("wechat_max_items must be non-negative")
    if wechat_min_items > resolved_wechat_max:
        raise ValueError("wechat_min_items must not exceed wechat_max_items")

    evaluation_time = now or datetime.now(timezone.utc)
    if evaluation_time.tzinfo is None:
        evaluation_time = evaluation_time.replace(tzinfo=timezone.utc)
    evaluation_time = evaluation_time.astimezone(timezone.utc)
    lower_bound = evaluation_time - timedelta(hours=freshness_hours)
    future_limit = evaluation_time + timedelta(minutes=5)

    # Build the complete ranked realtime pool first so matching signals
    # can corroborate a dedicated entry even when that duplicate is not
    # rendered in its own source section.
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
    hackernews = _take_source_entries(
        available_news, source="hackernews", limit=hackernews_items
    )
    owned_keys = set(dedicated_keys)
    for entry in hackernews:
        owned_keys.update(_entry_keys(entry))
    remaining = [entry for entry in available_news if not (_entry_keys(entry) & owned_keys)]
    wechat = _take_source_entries(remaining, source="wechat", limit=resolved_wechat_max)
    for entry in wechat:
        owned_keys.update(_entry_keys(entry))
    remaining = [entry for entry in available_news if not (_entry_keys(entry) & owned_keys)]
    x_entries = _take_source_entries(remaining, source="x", limit=x_items)

    for lane, bucket in (
        ("hackernews", hackernews),
        ("wechat", wechat),
        ("x", x_entries),
    ):
        for entry in bucket:
            entry.lane = lane
            entry.timestamp_field = "published_at"

    return DailyBriefingSelection(
        papers=papers,
        github=github,
        hackernews=hackernews,
        wechat=wechat,
        x=x_entries,
        expected_hackernews=hackernews_items,
        expected_wechat=wechat_min_items,
        max_wechat=resolved_wechat_max,
        expected_x=x_items,
        expected_github=github_items,
        expected_papers=paper_items,
        quota_mode=quota_mode,
    )
