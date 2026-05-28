from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

_DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "output"

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
    {"id": "dashboard", "label": "Dashboard", "description": "View local archive stats, coverage gaps, and recent briefings"},
    {"id": "library", "label": "Library", "description": "Search and browse your local research items"},
    {"id": "briefing", "label": "Briefing Workspace", "description": "Generate digest or reading list from your archive"},
    {"id": "collect", "label": "Collect Workspace", "description": "Collect research material from GitHub, papers, and WeChat"},
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
    page: int = 1,
    page_size: int = 20,
) -> dict[str, object]:
    all_items = [
        _item_to_payload(item)
        for item in query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
    ]
    total_count = len(all_items)
    total_pages = max(1, (total_count + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": all_items[start:end],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


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


COLLECT_SOURCE_FORMS: dict[str, dict[str, object]] = {
    "github": {
        "id": "github",
        "label": "GitHub",
        "description": "Collect from GitHub repositories",
        "fields": [
            {"name": "query", "label": "Search Query", "type": "text", "placeholder": "owner/repo or search keywords"},
            {"name": "search", "label": "Search Mode", "type": "boolean", "description": "Enable search mode instead of single repo"},
            {"name": "max", "label": "Max Results", "type": "number", "default": 10},
        ],
    },
    "papers": {
        "id": "papers",
        "label": "arXiv Papers",
        "description": "Collect from arXiv papers",
        "fields": [
            {"name": "category", "label": "Category", "type": "text", "placeholder": "cs.AI, cs.LG, cs.CL..."},
            {"name": "max", "label": "Max Results", "type": "number", "default": 10},
        ],
    },
    "wechat": {
        "id": "wechat",
        "label": "WeChat Articles",
        "description": "Collect WeChat public account articles",
        "fields": [
            {"name": "url", "label": "Article URL", "type": "text", "placeholder": "https://mp.weixin.qq.com/s/..."},
        ],
    },
}


def list_collect_sources() -> list[dict[str, object]]:
    """Return all available collect sources with their form definitions."""
    return list(COLLECT_SOURCE_FORMS.values())


def get_collect_form(source: str) -> dict[str, object]:
    """Return the form definition for a specific collect source."""
    if source not in COLLECT_SOURCE_FORMS:
        return {"id": source, "label": source, "description": "Unknown source", "fields": []}
    return dict(COLLECT_SOURCE_FORMS[source])


def run_collect(source: str, fields: dict[str, object], output_root: Path | None = None) -> dict[str, object]:
    """Run a collect operation for the given source with provided fields.

    Returns a dict with 'status', 'message', 'item_count', and 'saved_paths'.
    """
    root = Path(output_root) if output_root is not None else _DEFAULT_OUTPUT_ROOT

    if source == "github":
        import collect.github as github_collect

        query = fields.get("query", "")
        max_results = int(fields.get("max", 10))
        search_mode = bool(fields.get("search", False))
        owner_repo = query.split("/")
        if search_mode:
            github_collect.run_gh(["search", "repos", query, "--limit", str(max_results)])
            return {"status": "success", "message": f"GitHub search for '{query}' completed", "item_count": 0, "saved_paths": []}
        elif len(owner_repo) == 2:
            github_collect.save_repo(owner_repo[0], owner_repo[1], root / "github")
            return {"status": "success", "message": f"Collected GitHub repo: {query}", "item_count": 1, "saved_paths": [f"output/github/{owner_repo[0]}-{owner_repo[1]}"]}
        else:
            return {"status": "error", "message": f"Invalid GitHub query format: {query}. Use 'owner/repo' or enable search mode.", "item_count": 0, "saved_paths": []}
    if source == "papers":
        import collect.papers as papers_collect

        category = fields.get("category", "cs.AI")
        max_results = int(fields.get("max", 10))
        papers = papers_collect.fetch_papers_by_category([category], max_results=max_results)
        papers_collect.save_papers(papers, category, root / "papers")
        return {"status": "success", "message": f"Collected {len(papers)} papers from {category}", "item_count": len(papers), "saved_paths": [f"output/papers/{category}"]}
    if source == "wechat":
        import collect.wechat as wechat_collect

        url = fields.get("url", "")
        if not url:
            return {"status": "error", "message": "WeChat collection requires a URL", "item_count": 0, "saved_paths": []}
        asyncio.run(wechat_collect.fetch_article(url, output_dir=root / "wechat"))
        return {"status": "success", "message": f"Collected WeChat article: {url}", "item_count": 1, "saved_paths": ["output/wechat/"]}
    return {"status": "error", "message": f"Unknown source: {source}", "item_count": 0, "saved_paths": []}