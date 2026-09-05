from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from ai_intel_station.briefing.markdown import write_markdown

from .items import ResearchItem
from .storage import load_research_items


CATALOG_SECTION = "library"


@dataclass(frozen=True)
class LibraryCatalog:
    item_count: int
    source_counts: dict[str, int]
    tag_count: int
    untagged_count: int
    undated_count: int
    duplicate_groups: int
    orphan_markdown_count: int
    paths: tuple[Path, ...]


def _item_datetime(item: ResearchItem) -> datetime | None:
    for value in (item.published_at, item.updated_at, item.discovered_at):
        if not value:
            continue
        text = value.strip()
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            continue
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
        return parsed
    return None


def _sorted_items(items: list[ResearchItem]) -> list[ResearchItem]:
    by_identity = sorted(
        items,
        key=lambda item: (item.source.lower(), item.title.lower(), item.canonical_url or ""),
    )
    return sorted(
        by_identity,
        key=lambda item: _item_datetime(item) or datetime.min,
        reverse=True,
    )


def _escape_text(value: str) -> str:
    return value.replace("\n", " ").replace("\r", " ").replace("]", "\\]")


def _resolve_item_path(item: ResearchItem, output_root: Path) -> Path | None:
    if not item.output_path:
        return None
    raw = Path(item.output_path)
    if raw.is_absolute():
        return raw.resolve()
    if raw.parts and raw.parts[0] == output_root.name:
        return (output_root.parent / raw).resolve()
    return (output_root / raw).resolve()


def _relative_catalog_link(target: Path, output_root: Path) -> str:
    try:
        relative = target.relative_to(output_root.resolve())
    except ValueError:
        return target.as_uri()
    catalog_relative = Path("../..") / relative
    return quote(catalog_relative.as_posix(), safe="/:%")


def _local_target(item: ResearchItem, output_root: Path) -> str | None:
    target = _resolve_item_path(item, output_root)
    return _relative_catalog_link(target, output_root) if target is not None else None


def _item_line(item: ResearchItem, output_root: Path) -> str:
    title = _escape_text(item.title)
    if item.canonical_url:
        rendered = f"[{title}](<{item.canonical_url}>)"
    else:
        rendered = title
    local = _local_target(item, output_root)
    if local:
        rendered += f" · [open local]({local})"
    return f"- [{item.source}] {rendered}"


def _render_index(
    items: list[ResearchItem],
    *,
    source_counts: Counter[str],
    tag_count: int,
    untagged_count: int,
    undated_count: int,
    duplicate_groups: int,
    orphan_markdown_count: int,
) -> str:
    lines = [
        "# Library Catalog",
        "",
        "> Derived from local `ResearchItem` sidecars; regenerate with `research organize`.",
        "",
        "## Organization model",
        "",
        "- Physical archive stays under `output/<source>/` using source-native identity.",
        "- Date and tag are browse dimensions, not folder ownership.",
        "- Topic is represented by explicit tag; the catalog never guesses topic from title text.",
        "- Duplicate canonical URLs remain visible for audit and are not automatically deleted.",
        "",
        "## Snapshot",
        "",
        "| Metric | Count |",
        "|:-------|------:|",
        f"| ResearchItem | {len(items)} |",
        f"| Source | {len(source_counts)} |",
        f"| Tag | {tag_count} |",
        f"| Untagged item | {untagged_count} |",
        f"| Undated item | {undated_count} |",
        f"| Duplicate URL group | {duplicate_groups} |",
        f"| Orphan Markdown | {orphan_markdown_count} |",
        "",
        "## Source coverage",
        "",
        "| Source | Items |",
        "|:-------|------:|",
    ]
    lines.extend(
        f"| {source} | {count} |"
        for source, count in sorted(source_counts.items(), key=lambda pair: (-pair[1], pair[0]))
    )
    lines.extend(
        [
            "",
            "## Browse",
            "",
            "- [By date](by-date.md)",
            "- [By tag](by-tag.md)",
            "- [Duplicate audit](duplicates.md)",
            "- [Orphan Markdown audit](orphans.md)",
        ]
    )
    return "\n".join(lines)


def _render_by_date(items: list[ResearchItem], output_root: Path) -> str:
    grouped: dict[str, list[ResearchItem]] = defaultdict(list)
    for item in items:
        timestamp = _item_datetime(item)
        grouped[timestamp.strftime("%Y-%m") if timestamp else "Unknown date"].append(item)

    known = sorted((key for key in grouped if key != "Unknown date"), reverse=True)
    order = known + (["Unknown date"] if "Unknown date" in grouped else [])
    lines = [
        "# Library by Date",
        "",
        "> Date uses `published_at`, then `updated_at`, then `discovered_at`.",
        "",
    ]
    for month in order:
        lines.extend([f"## {month}", ""])
        for item in _sorted_items(grouped[month]):
            lines.append(_item_line(item, output_root))
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_by_tag(items: list[ResearchItem], output_root: Path) -> str:
    grouped: dict[str, list[ResearchItem]] = defaultdict(list)
    untagged: list[ResearchItem] = []
    for item in items:
        tags = sorted(set(item.tags), key=str.lower)
        if not tags:
            untagged.append(item)
            continue
        for tag in tags:
            grouped[tag].append(item)

    order = sorted(grouped, key=lambda tag: (-len(grouped[tag]), tag.lower()))
    lines = [
        "# Library by Tag",
        "",
        "> Tags come from source metadata or explicit curation; no topic is inferred from title text.",
        "",
    ]
    for tag in order:
        lines.extend([f"## {tag} ({len(grouped[tag])})", ""])
        for item in _sorted_items(grouped[tag]):
            lines.append(_item_line(item, output_root))
        lines.append("")

    if untagged:
        lines.extend([f"## Untagged ({len(untagged)})", ""])
        for item in _sorted_items(untagged):
            lines.append(_item_line(item, output_root))
    return "\n".join(lines).rstrip()


def _duplicate_groups(items: list[ResearchItem]) -> list[tuple[str, list[ResearchItem]]]:
    grouped: dict[str, list[ResearchItem]] = defaultdict(list)
    for item in items:
        if item.canonical_url:
            grouped[item.canonical_url].append(item)
    return sorted(
        ((url, group) for url, group in grouped.items() if len(group) > 1),
        key=lambda pair: (-len(pair[1]), pair[0]),
    )


def _render_duplicates(
    groups: list[tuple[str, list[ResearchItem]]],
    output_root: Path,
) -> str:
    lines = [
        "# Duplicate Audit",
        "",
        "> A duplicate URL can represent valid cross-category or cross-feed context. This report does not delete data.",
        "",
    ]
    if not groups:
        lines.append("No duplicate canonical URL found.")
        return "\n".join(lines)
    for url, items in groups:
        lines.extend([f"## {_escape_text(items[0].title)}", "", f"Canonical URL: <{url}>", ""])
        for item in _sorted_items(items):
            lines.append(_item_line(item, output_root))
        lines.append("")
    return "\n".join(lines).rstrip()


def _orphan_markdown(items: list[ResearchItem], output_root: Path) -> list[Path]:
    referenced = {
        target
        for item in items
        if (target := _resolve_item_path(item, output_root)) is not None
    }
    return sorted(
        path.resolve()
        for path in output_root.rglob("*.md")
        if "briefing" not in path.relative_to(output_root).parts
        if path.resolve() not in referenced
    )


def _render_orphans(paths: list[Path], output_root: Path) -> str:
    lines = [
        "# Orphan Markdown Audit",
        "",
        "> These files are not referenced by any loaded `ResearchItem` sidecar. Review them before backfill, move, or deletion.",
        "",
    ]
    if not paths:
        lines.append("No orphan Markdown found.")
        return "\n".join(lines)
    for path in paths:
        relative = path.relative_to(output_root).as_posix()
        lines.append(f"- [{_escape_text(relative)}]({_relative_catalog_link(path, output_root)})")
    return "\n".join(lines)


def build_library_catalog(output_root: Path) -> LibraryCatalog:
    output_root = Path(output_root).resolve()
    items = load_research_items(output_root)
    source_counts = Counter(item.source for item in items)
    unique_tags = {tag for item in items for tag in item.tags}
    untagged_count = sum(not item.tags for item in items)
    undated_count = sum(_item_datetime(item) is None for item in items)
    duplicates = _duplicate_groups(items)
    orphans = _orphan_markdown(items, output_root)
    catalog_dir = output_root / "briefing" / CATALOG_SECTION
    paths = (
        write_markdown(
            catalog_dir / "index.md",
            _render_index(
                items,
                source_counts=source_counts,
                tag_count=len(unique_tags),
                untagged_count=untagged_count,
                undated_count=undated_count,
                duplicate_groups=len(duplicates),
                orphan_markdown_count=len(orphans),
            ),
        ),
        write_markdown(catalog_dir / "by-date.md", _render_by_date(items, output_root)),
        write_markdown(catalog_dir / "by-tag.md", _render_by_tag(items, output_root)),
        write_markdown(
            catalog_dir / "duplicates.md",
            _render_duplicates(duplicates, output_root),
        ),
        write_markdown(catalog_dir / "orphans.md", _render_orphans(orphans, output_root)),
    )
    return LibraryCatalog(
        item_count=len(items),
        source_counts=dict(source_counts),
        tag_count=len(unique_tags),
        untagged_count=untagged_count,
        undated_count=undated_count,
        duplicate_groups=len(duplicates),
        orphan_markdown_count=len(orphans),
        paths=paths,
    )
