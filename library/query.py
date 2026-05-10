from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .items import ResearchItem
from .storage import load_research_items


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _matches_keyword(item: ResearchItem, keyword: str | None) -> bool:
    if not keyword:
        return True

    haystack = " ".join(
        [item.title, item.summary or "", " ".join(item.tags), " ".join(item.authors)]
    ).lower()
    return keyword.lower() in haystack


def _matches_sources(item: ResearchItem, sources: list[str] | None) -> bool:
    if not sources:
        return True
    source_set = {source.lower() for source in sources}
    return item.source.lower() in source_set


def _matches_time_window(item: ResearchItem, since: str | None, until: str | None) -> bool:
    if not since and not until:
        return True

    item_time = _parse_datetime(item.published_at) or _parse_datetime(item.updated_at)
    if item_time is None:
        return False

    since_dt = _parse_datetime(since)
    until_dt = _parse_datetime(until)
    if since_dt and item_time < since_dt:
        return False
    if until_dt and item_time > until_dt:
        return False
    return True


def query_research_items(
    output_root: Path,
    keyword: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[ResearchItem]:
    items = load_research_items(output_root)
    matches = [
        item
        for item in items
        if _matches_keyword(item, keyword)
        and _matches_sources(item, sources)
        and _matches_time_window(item, since, until)
    ]
    return sorted(
        matches,
        key=lambda item: (
            _parse_datetime(item.published_at) or _parse_datetime(item.updated_at) or datetime.min,
            item.title.lower(),
        ),
        reverse=True,
    )
