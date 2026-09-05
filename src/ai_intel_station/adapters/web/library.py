from __future__ import annotations

from pathlib import Path

from ai_intel_station.library.service import find_library_item, item_to_payload, search_library
from ai_intel_station.library.storage import load_research_items


_SEARCH_NOTES = {
    "scope": "Library only searches the local archive and ResearchItem sidecar. It never triggers a remote fetch against GitHub, arXiv, or WeChat.",
    "filter": "Keyword, Sources, and Since / Until filters all act on already-saved local items — they do not reach out to the network.",
    "result_source": "Each result comes from output/ in the local archive and links to the saved Markdown.",
}


def library_search_notes() -> dict[str, str]:
    return dict(_SEARCH_NOTES)


def list_library_items(
    output_root: Path,
    keyword: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, object]:
    all_items = [
        item_to_payload(item)
        for item in search_library(
            output_root,
            keyword=keyword,
            sources=sources,
            since=since,
            until=until,
        )
    ]
    total_count = len(all_items)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    result: dict[str, object] = {
        "items": all_items[start : start + page_size],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "search_notes": library_search_notes(),
    }
    if total_count == 0:
        result["empty_state"] = {
            "explanation": "No local ResearchItems matched your search. Library only searches what is already on disk.",
            "next_steps": [
                "Try a broader keyword, clear the date range, or include more sources.",
                "Visit Collect Workspace to pull in more material from GitHub, arXiv, or WeChat.",
            ],
        }
    return result


def get_library_item_detail(output_root: Path, output_path: str) -> dict[str, object] | None:
    item = find_library_item(output_root, output_path)
    return item_to_payload(item) if item is not None else None


class PreviewError(Exception):
    """A requested preview escaped the permitted local archive boundary."""


def read_item_markdown(output_root: Path, output_path: str) -> tuple[str, str]:
    output_root = Path(output_root).resolve()
    project_root = output_root.parent
    requested = Path(output_path)
    if requested.is_absolute():
        candidate = requested.resolve()
    else:
        candidate = (project_root / requested).resolve()
        if output_root != candidate and output_root not in candidate.parents:
            candidate = (output_root / requested).resolve()
    try:
        candidate.relative_to(output_root)
    except ValueError as exc:
        raise PreviewError(f"Refusing to read outside output_root: {output_path!r}") from exc

    candidate_rel = candidate.relative_to(output_root).as_posix()
    known_paths: set[str] = set()
    for item in load_research_items(output_root):
        if not item.output_path:
            continue
        known_abs = (project_root / item.output_path).resolve()
        try:
            known_paths.add(known_abs.relative_to(output_root).as_posix())
        except ValueError:
            continue
    if candidate_rel not in known_paths:
        raise FileNotFoundError(
            f"Refusing: {output_path!r} is not a known archive entry. "
            "Only sidecar output_paths are readable."
        )
    if not candidate.is_file():
        raise FileNotFoundError(f"Markdown file missing: {output_path!r}")
    return candidate.read_text(encoding="utf-8", errors="replace"), "text/markdown; charset=utf-8"
