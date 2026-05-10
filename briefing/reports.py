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


def build_digest_markdown(title: str, items: list[ResearchItem], requested_sources: list[str] | None = None) -> str:
    lines = [f"# Digest: {title}", "", "> Source: local research library", ""]
    lines.extend(_coverage_note(items, requested_sources))

    for source, grouped_items in _grouped_items(items).items():
        lines.extend([f"## {source}", ""])
        for item in grouped_items:
            lines.append(f"- [{item.title}]({item.canonical_url or ''})")
            if item.summary:
                lines.append(f"  - {item.summary}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_reading_list_markdown(title: str, items: list[ResearchItem], requested_sources: list[str] | None = None) -> str:
    lines = [f"# Reading List: {title}", "", "> Source: local research library", ""]
    lines.extend(_coverage_note(items, requested_sources))

    for source, grouped_items in _grouped_items(items).items():
        lines.extend([f"## {source}", ""])
        for item in grouped_items:
            lines.append(f"- [ ] [{item.title}]({item.canonical_url or ''})")
            if item.summary:
                lines.append(f"  - {item.summary}")
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
