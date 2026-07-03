from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from library.items import ResearchItem
from publish.obsidian import briefing_output_path, write_markdown


def _sort_items(items: list[ResearchItem]) -> list[ResearchItem]:
    return sorted(items, key=lambda item: (item.source.lower(), item.title.lower()))


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
    from library.items import REPO_ROOT

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

    `[label](url)` parses greedily — any literal ']' inside the label
    closes the link early. Replace with '\\]'. Other markdown
    characters ('\\', '(', ')') are uncommon in ResearchItem fields
    and dealt with by markdown renderers without breaking the link.
    """
    return value.replace("]", "\\]")


def _format_item(item: ResearchItem, *, checked: bool) -> list[str]:
    """Render a single ResearchItem as a list of markdown lines.

    Always shows the external link first; if the item has a local markdown
    archive, appends a separate "(open local)" link on the same bullet so
    Obsidian users can open the in-vault copy directly.
    """
    title = _escape_link_text(item.title)
    external = _escape_link_text(item.canonical_url or "")
    marker = "[ ]" if checked else ""

    local = _local_link(item)
    if local:
        # Two links on one bullet line; Obsidian renders both.
        title_with_links = f"[{title}]({external}) · [open local]({local})"
    else:
        title_with_links = f"[{title}]({external})"

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


def write_digest_report(
    output_root: Path,
    title: str,
    items: list[ResearchItem],
    requested_sources: list[str] | None = None,
) -> Path:
    path = briefing_output_path(output_root, "digests", title)
    return write_markdown(path, build_digest_markdown(title, items, requested_sources=requested_sources))


def write_reading_list_report(
    output_root: Path,
    title: str,
    items: list[ResearchItem],
    requested_sources: list[str] | None = None,
) -> Path:
    path = briefing_output_path(output_root, "reading-lists", title)
    return write_markdown(path, build_reading_list_markdown(title, items, requested_sources=requested_sources))
