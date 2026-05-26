from __future__ import annotations

from datetime import datetime
from pathlib import Path

from briefing.reports import (
    build_digest_markdown,
    build_reading_list_markdown,
    write_digest_report,
    write_reading_list_report,
)
from library.query import query_research_items
from library.storage import load_research_items


SUPPORTED_SOURCES = ("github", "papers", "wechat")
PHASE_ONE_SECTIONS = (
    {"id": "dashboard", "label": "Dashboard"},
    {"id": "library", "label": "Library"},
    {"id": "briefing", "label": "Briefing Workspace"},
)


def workspace_sections() -> list[dict[str, str]]:
    return list(PHASE_ONE_SECTIONS)


def _relative_output_path(output_root: Path, path: Path) -> str:
    return path.relative_to(output_root.parent).as_posix()


def _source_counts(output_root: Path) -> dict[str, int]:
    counts = {source: 0 for source in SUPPORTED_SOURCES}
    for item in load_research_items(output_root):
        if item.source in counts:
            counts[item.source] += 1
    return {source: count for source, count in counts.items() if count}


def _orphan_markdown_paths(output_root: Path) -> list[str]:
    output_root = Path(output_root)
    known_paths = {
        item.output_path
        for item in load_research_items(output_root)
        if item.output_path and item.output_path.startswith("output/")
    }
    orphan_paths = []
    for path in output_root.glob("**/*.md"):
        if "briefing" in path.parts:
            continue
        relative_path = _relative_output_path(output_root, path)
        if relative_path not in known_paths:
            orphan_paths.append(relative_path)
    return sorted(orphan_paths)


def _recent_briefings(output_root: Path, limit: int = 5) -> list[dict[str, str]]:
    briefing_root = Path(output_root) / "briefing"
    if not briefing_root.exists():
        return []

    paths = sorted(briefing_root.glob("**/*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    recent = []
    for path in paths[:limit]:
        first_line = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        recent.append(
            {
                "title": first_line or path.stem,
                "path": _relative_output_path(output_root, path),
                "section": path.parent.name,
            }
        )
    return recent


def build_dashboard_overview(output_root: Path) -> dict[str, object]:
    output_root = Path(output_root)
    items = load_research_items(output_root)
    source_counts = _source_counts(output_root)
    orphan_markdown_paths = _orphan_markdown_paths(output_root)
    missing_sources = [source for source in SUPPORTED_SOURCES if source_counts.get(source, 0) == 0]
    return {
        "total_items": len(items),
        "source_counts": source_counts,
        "missing_sources": missing_sources,
        "orphan_markdown_paths": orphan_markdown_paths,
        "recent_briefings": _recent_briefings(output_root),
    }


def _item_to_payload(item) -> dict[str, object]:
    return {
        "source": item.source,
        "item_type": item.item_type,
        "title": item.title,
        "canonical_url": item.canonical_url,
        "summary": item.summary,
        "authors": item.authors,
        "published_at": item.published_at,
        "updated_at": item.updated_at,
        "tags": item.tags,
        "output_path": item.output_path,
        "metadata": item.metadata,
    }


def list_library_items(
    output_root: Path,
    keyword: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, object]]:
    return [
        _item_to_payload(item)
        for item in query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
    ]


def get_library_item_detail(output_root: Path, output_path: str) -> dict[str, object] | None:
    for item in load_research_items(output_root):
        if item.output_path == output_path:
            return _item_to_payload(item)
    return None


def _briefing_content(
    mode: str,
    output_root: Path,
    keyword: str,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> tuple[str, list[object]]:
    items = query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
    resolved_title = title or keyword
    if mode == "digest":
        content = build_digest_markdown(resolved_title, items, requested_sources=sources)
    else:
        content = build_reading_list_markdown(resolved_title, items, requested_sources=sources)
    return content, items


def preview_briefing(
    output_root: Path,
    mode: str,
    keyword: str,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, object]:
    content, items = _briefing_content(
        mode,
        output_root,
        keyword,
        title=title,
        sources=sources,
        since=since,
        until=until,
    )
    return {
        "title": title or keyword,
        "mode": mode,
        "content": content,
        "item_count": len(items),
    }


def save_briefing(
    output_root: Path,
    mode: str,
    keyword: str,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, object]:
    items = query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
    resolved_title = title or keyword
    if mode == "digest":
        path = write_digest_report(output_root, title=resolved_title, items=items, requested_sources=sources)
    else:
        path = write_reading_list_report(output_root, title=resolved_title, items=items, requested_sources=sources)
    return {
        "title": resolved_title,
        "mode": mode,
        "path": path.as_posix(),
        "content": path.read_text(encoding="utf-8"),
        "saved_at": datetime.utcnow().isoformat() + "Z",
    }