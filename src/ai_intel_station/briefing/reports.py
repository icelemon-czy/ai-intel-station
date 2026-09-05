from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from pathlib import Path

from ai_intel_station.library.items import ResearchItem
from ai_intel_station.library.query import item_datetime


def _sort_items(items: list[ResearchItem]) -> list[ResearchItem]:
    """Sort within a source group: newest first, then title-ascending.

    briefing/reports.py mirrors the library.query sort contract so the
    most-recent-first ordering carries through from the saved
    archive into the rendered brief. Previously this was alphabetical,
    meaning a digest always opened with whatever happened to sort
    first — usually a 2-year-old generic write-up that nobody wanted.
    """
    by_title = sorted(items, key=lambda item: item.title.lower())
    return sorted(
        by_title,
        key=lambda item: item_datetime(item) or datetime.min,
        reverse=True,
    )


def _coverage_note(items: list[ResearchItem], requested_sources: list[str] | None) -> list[str]:
    lines = []
    if not requested_sources:
        return lines

    available = {item.source for item in items}
    missing = [source for source in requested_sources if source not in available]
    if missing:
        lines.extend(["## Coverage Notes", "", f"Missing sources: {', '.join(missing)}", ""])
    return lines


def _grouped_items(items: list[ResearchItem]) -> dict[str, list[ResearchItem]]:
    grouped = defaultdict(list)
    for item in _sort_items(items):
        grouped[item.source].append(item)
    return dict(grouped)


def _local_link(item: ResearchItem) -> str | None:
    """Return a relative path from a briefing markdown to the local markdown
    archive entry for ``item``, or ``None`` when no archive exists.

    The briefing markdown lives at ``<output_root>/briefing/<section>/<title>.md``
    and the archive lives at ``<output_root>/<source>/...``. The local link is
    therefore ``../../<archive_rel_path>`` where ``archive_rel_path`` is the
    item's ``output_path`` relative to REPO_ROOT, stripped of its leading
    ``output/`` segment.

    Falls back to an absolute ``file://`` URL when the path cannot be made
    relative — never returns a broken relative link.
    """
    if not item.output_path:
        return None
    from ai_intel_station.library.items import REPO_ROOT

    raw = Path(item.output_path)
    if not raw.is_absolute():
        raw = REPO_ROOT / raw
    try:
        rel_to_repo = raw.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        # Output path is outside REPO_ROOT (test env, custom layout). We still
        # surface a usable link via file:// so the user can click through.
        return raw.as_uri()

    # Strip the leading "output/" segment so the link re-anchors from the
    # briefing location (which is at <repo>/output/briefing/...).
    if rel_to_repo.startswith("output/"):
        archive = rel_to_repo[len("output/"):]
    elif rel_to_repo.startswith("./output/"):
        archive = rel_to_repo[len("./output/"):]
    else:
        # Already lives outside output/ — leave as-is.
        archive = rel_to_repo
    return f"../../{archive}"


def _escape_link_text(value: str) -> str:
    """Escape ']' inside a markdown link text.

    Multi-line input is collapsed onto a single line so the bullet
    does not break into a multi-line item that escapes its parent
    list. A title with '\\n' makes the bullet split across multiple
    rendered lines that a Markdown viewer treats as siblings of the parent
    bullet rather than continuation.

    A line with backslash-period is also escaped (``\\.``) — markdown
    frontmatter/start-of-extension markers should not appear inside a
    link label.
    """
    flat = value.replace("\n", " ").replace("\r", " ")
    flat = flat.replace("]", "\\]")
    # Escape backslash-period which CommonMark parses as
    # an extension escape sequence.
    flat = flat.replace("\\.", "\\\\.")
    return flat


def _format_item(item: ResearchItem, *, checked: bool) -> list[str]:
    """Render a single ResearchItem as a list of markdown lines.

    Always shows the external link first; if the item has a local markdown
    archive, appends a separate "(open local)" link on the same bullet so
    the local archive copy can be opened from the same bullet.

    An item without a canonical URL renders with the title as plain
    text (no markdown link) — emitting an empty ``[title]()`` would
    render as a broken Markdown anchor. The URL is NOT escaped
    (only the title is) so the link target remains the literal URL.
    """
    title = _escape_link_text(item.title)
    external = (item.canonical_url or "").strip()
    marker = "[ ]" if checked else ""

    local = _local_link(item)
    if external:
        link_part = f"[{title}]({external})"
    else:
        link_part = title
    if local:
        # Two links on one bullet line; Markdown renders both.
        title_with_links = f"{link_part} · [open local]({local})"
    else:
        title_with_links = link_part

    lines = [f"- {marker} {title_with_links}"]
    if item.summary:
        # Summaries routinely span multiple lines on arXiv abstracts.
        # Indent every continuation line so the bullet does not break
        # into sibling list items when the page renders.
        joined = item.summary.replace("\n", "\n    ")
        lines.append(f"  - {joined}")
    if item.authors:
        # Surface up to 3 authors; longer lists fall back to the first + count.
        authors = ", ".join(item.authors[:3])
        if len(item.authors) > 3:
            authors += f" … (+{len(item.authors) - 3} more)"
        lines.append(f"  - _{authors}_")
    return lines


def build_digest_markdown(title: str, items: list[ResearchItem], requested_sources: list[str] | None = None) -> str:
    lines = [f"# Digest: {title}", "", "> Source: local research library", ""]
    lines.extend(_coverage_note(items, requested_sources))

    for source, grouped_items in _grouped_items(items).items():
        lines.extend([f"## {source}", ""])
        for item in grouped_items:
            lines.extend(_format_item(item, checked=False))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_reading_list_markdown(title: str, items: list[ResearchItem], requested_sources: list[str] | None = None) -> str:
    lines = [f"# Reading List: {title}", "", "> Source: local research library", ""]
    lines.extend(_coverage_note(items, requested_sources))

    for source, grouped_items in _grouped_items(items).items():
        lines.extend([f"## {source}", ""])
        for item in grouped_items:
            lines.extend(_format_item(item, checked=True))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
