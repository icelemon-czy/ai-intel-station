from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .items import ResearchItem
from .storage import load_research_items


def _parse_datetime(value: str | None) -> datetime | None:
    """Return a datetime for ``value`` or None when the input is empty.

    Raises ``ValueError`` when the input is non-empty but does not parse.
    Callers should treat that as a hard failure so the user is told their
    filter format is wrong — silently returning None here would let
    ``since=garbage`` behave like ``since is unset``, masking what
    should be a 4xx.
    """
    if not value:
        return None
    if not isinstance(value, str):
        raise ValueError(f"expected a string, got {type(value).__name__}")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"unparseable datetime {value!r}; expected ISO-8601 (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)"
    )


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

    # Item-side dates are pulled from real-world data, so they may be
    # anything. If we can't parse them, the safe fallback is "include
    # the item" — _parse_datetime here will only raise for malformed
    # USER input (since/until), which the caller surfaces upstream.
    try:
        item_time = _parse_datetime(item.published_at) or _parse_datetime(item.updated_at)
    except ValueError:
        item_time = None
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
    # Validate since/until BEFORE walking the archive so a malformed
    # user filter raises even when the archive is empty (or all items
    # happen to be filtered out by keyword/sources). The CLI used to
    # silently return "no matches" in that case — the user typed
    # nonsense and got an empty result with no signal.
    if since:
        _parse_datetime(since)  # raises ValueError on garbage
    if until:
        _parse_datetime(until)

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
