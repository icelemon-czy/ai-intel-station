from __future__ import annotations

from pathlib import Path

from .backfill import backfill_output_tree
from .catalog import LibraryCatalog, build_library_catalog
from .items import ResearchItem
from .query import query_research_items
from .storage import load_research_items


def item_to_payload(item: ResearchItem) -> dict[str, object]:
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


def display_archive_path(path: str | Path, output_root: Path) -> str:
    """返回 archive path；custom root 仍以其 parent 为显示锚点。"""

    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(Path(output_root).resolve().parent).as_posix()
    except ValueError:
        return resolved.as_posix()


def search_library(
    output_root: Path,
    *,
    keyword: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[ResearchItem]:
    return query_research_items(
        output_root,
        keyword=keyword,
        sources=sources,
        since=since,
        until=until,
    )


def _path_suffix(path: str | None) -> str:
    parts = Path(path or "").parts
    return "/".join(parts[-2:]) if len(parts) >= 2 else (path or "")


def find_library_item(output_root: Path, output_path: str) -> ResearchItem | None:
    target = _path_suffix(output_path)
    return next(
        (item for item in load_research_items(output_root) if _path_suffix(item.output_path) == target),
        None,
    )


def backfill_library(output_root: Path) -> list[Path]:
    return backfill_output_tree(output_root)


def organize_library(output_root: Path) -> LibraryCatalog:
    """生成可重建的 date/tag/duplicate catalog，不移动 primary archive。"""

    return build_library_catalog(output_root)
