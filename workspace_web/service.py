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
    {
        "id": "dashboard",
        "label": "Dashboard",
        "description": "View local archive stats, coverage gaps, and recent briefings",
        "purpose": "See the health of your local ResearchItem archive at a glance.",
        "reads": "Local ResearchItem sidecars under output/ and recent briefing files under output/briefing/.",
        "produces": "An at-a-glance view of total items, source coverage, missing sources, and recent briefings.",
    },
    {
        "id": "library",
        "label": "Library",
        "description": "Search and browse your local research items",
        "purpose": "Find and inspect items already saved to your local archive.",
        "reads": "Local ResearchItem sidecars under output/ only — never a remote source.",
        "produces": "Filtered lists and per-item detail with a link to the saved Markdown.",
    },
    {
        "id": "briefing",
        "label": "Briefing Workspace",
        "description": "Generate digest or reading list from your archive",
        "purpose": "Turn local items into a digest or reading list you can read or save.",
        "reads": "Local ResearchItem sidecars matching your keyword / sources / date filters.",
        "produces": "A previewable Markdown briefing and, on Save, a file under output/briefing/.",
    },
    {
        "id": "collect",
        "label": "Collect Workspace",
        "description": "Collect research material from GitHub, papers, and WeChat",
        "purpose": "Pull new material from GitHub, arXiv, or WeChat into the local archive.",
        "reads": "Your source-specific inputs (owner/repo, arXiv category, or WeChat URL).",
        "produces": "New ResearchItem sidecars and Markdown files under output/<source>/.",
    },
)


def workspace_sections() -> list[dict[str, str]]:
    return list(PHASE_ONE_SECTIONS)


def page_purpose_cards() -> list[dict[str, str]]:
    """Return a list of page-purpose cards, one per workspace section."""
    return [
        {
            "id": section["id"],
            "title": section["label"],
            "purpose": section["purpose"],
            "reads": section["reads"],
            "produces": section["produces"],
        }
        for section in PHASE_ONE_SECTIONS
    ]


_BRIEFING_MODE_PURPOSES: dict[str, str] = {
    "digest": "Summarize the matching local items into a short digest you can read end-to-end.",
    "reading-list": "Queue the matching local items into a reading list for later review.",
}


_BRIEFING_ACTION_PURPOSES: dict[str, str] = {
    "preview": "Show the derived Markdown in-page only. Does not write any file.",
    "save": "Write the derived Markdown to output/briefing/ as a saved reading artifact.",
}


_BRIEFING_FLOW_NOTES: dict[str, str] = {
    "input_source": "Briefings are generated from the local Library / ResearchItem sidecar only — no remote fetch happens here.",
    "preview_vs_save": "Preview keeps the result in this panel. Save persists a Markdown file to output/briefing/.",
    "saved_artifact": "Saved files are derived reading artifacts, not new primary research items.",
}


def briefing_mode_purposes() -> dict[str, str]:
    return dict(_BRIEFING_MODE_PURPOSES)


def briefing_action_purposes() -> dict[str, str]:
    return dict(_BRIEFING_ACTION_PURPOSES)


def briefing_flow_notes() -> dict[str, str]:
    return dict(_BRIEFING_FLOW_NOTES)


_LIBRARY_SEARCH_NOTES: dict[str, str] = {
    "scope": "Library only searches the local archive and ResearchItem sidecar. It never triggers a remote fetch against GitHub, arXiv, or WeChat.",
    "filter": "Keyword, Sources, and Since / Until filters all act on already-saved local items — they do not reach out to the network.",
    "result_source": "Each result comes from output/ in the local archive and links to the saved Markdown.",
}


def library_search_notes() -> dict[str, str]:
    return dict(_LIBRARY_SEARCH_NOTES)


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
    overview: dict[str, object] = {
        "total_items": len(items),
        "source_counts": source_counts,
        "missing_sources": missing_sources,
        "orphan_markdown_paths": orphan_markdown_paths,
        "recent_briefings": _recent_briefings(output_root),
    }
    if not items:
        overview["empty_state"] = {
            "explanation": "Your local archive is empty. Nothing has been collected yet.",
            "next_steps": [
                "Open Collect Workspace and run a manual collect for GitHub, arXiv Papers, or WeChat.",
                "Or run `uv run research backfill output` to rebuild the local archive from existing files.",
            ],
        }
    return overview


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
    result: dict[str, object] = {
        "items": all_items[start:end],
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
    result: dict[str, object] = {
        "title": title or keyword,
        "mode": mode,
        "content": content,
        "item_count": len(items),
    }
    if not items:
        result["empty_state"] = {
            "explanation": "Briefing is derived from the local ResearchItem archive. No items matched your filters.",
            "next_steps": [
                "Loosen the keyword / sources / date range and try preview again.",
                "Use Collect Workspace or `uv run research backfill output` to add more material first.",
            ],
        }
    return result


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
        "purpose": "Snapshot a single repository or pull a batch of repos from a search query.",
        "required_input": "owner/repo (single repo) OR search keyword with search mode enabled",
        "output_dir": "output/github/",
        "dependency_hint": "Requires the GitHub CLI (`gh`) to be installed and authenticated.",
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
        "purpose": "Pull paper abstracts and metadata for one or more arXiv categories.",
        "required_input": "arXiv category code (e.g. cs.AI) and maximum number of results",
        "output_dir": "output/papers/",
        "dependency_hint": "Uses the arXiv public API; no API key or authentication required.",
        "fields": [
            {"name": "category", "label": "Category", "type": "text", "placeholder": "cs.AI, cs.LG, cs.CL..."},
            {"name": "max", "label": "Max Results", "type": "number", "default": 10},
        ],
    },
    "wechat": {
        "id": "wechat",
        "label": "WeChat Articles",
        "description": "Collect WeChat public account articles",
        "purpose": "Fetch a single WeChat public account article as local Markdown.",
        "required_input": "WeChat article URL (mp.weixin.qq.com)",
        "output_dir": "output/wechat/",
        "dependency_hint": "Uses the Camoufox anti-detection browser runtime; first run may be slow.",
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


def _format_collect_result(
    source: str,
    status: str,
    message: str,
    summary: str,
    next_step: str,
    item_count: int = 0,
    saved_paths: list[str] | None = None,
    extra_details: dict[str, object] | None = None,
) -> dict[str, object]:
    """Wrap a raw collect outcome into the standardized result shape.

    The legacy fields (`status`, `message`, `item_count`, `saved_paths`) are kept so
    existing callers and tests keep working. New callers can rely on `summary`,
    `next_step`, and `details` for the human-readable layer.
    """
    details: dict[str, object] = {"item_count": item_count, "saved_paths": list(saved_paths or [])}
    if extra_details:
        details.update(extra_details)
    return {
        "status": status,
        "message": message,
        "item_count": item_count,
        "saved_paths": list(saved_paths or []),
        "source": source,
        "summary": summary,
        "next_step": next_step,
        "details": details,
    }


def run_collect(source: str, fields: dict[str, object], output_root: Path | None = None) -> dict[str, object]:
    """Run a collect operation for the given source with provided fields.

    Returns a dict with 'status', 'message', 'item_count', 'saved_paths',
    and the standardized 'summary' / 'next_step' / 'details' fields.
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
            return _format_collect_result(
                source="github",
                status="success",
                message=f"GitHub search for '{query}' completed",
                summary=f"GitHub search for '{query}' finished. Up to {max_results} repos were considered.",
                next_step="Open the Library page to browse the new repos once they are persisted.",
                item_count=0,
                saved_paths=[],
                extra_details={"query": query, "max_results": max_results, "search_mode": True},
            )
        elif len(owner_repo) == 2:
            owner, repo = owner_repo
            github_collect.save_repo(owner, repo, root / "github")
            return _format_collect_result(
                source="github",
                status="success",
                message=f"Collected GitHub repo: {query}",
                summary=f"Saved GitHub repository {owner}/{repo} to output/github/.",
                next_step="Open the Library page to inspect the saved repo Markdown and sidecar.",
                item_count=1,
                saved_paths=[f"output/github/{owner}-{repo}"],
                extra_details={"owner": owner, "repo": repo},
            )
        else:
            return _format_collect_result(
                source="github",
                status="error",
                message=f"Invalid GitHub query format: {query}. Use 'owner/repo' or enable search mode.",
                summary=f"GitHub query '{query}' is not in 'owner/repo' format and search mode is off.",
                next_step="Switch the source to GitHub, then either enter 'owner/repo' or enable Search Mode with a keyword.",
                item_count=0,
                saved_paths=[],
                extra_details={"query": query, "search_mode": search_mode},
            )
    if source == "papers":
        import collect.papers as papers_collect

        category = fields.get("category", "cs.AI")
        max_results = int(fields.get("max", 10))
        papers = papers_collect.fetch_papers_by_category([category], max_results=max_results)
        papers_collect.save_papers(papers, category, root / "papers")
        return _format_collect_result(
            source="papers",
            status="success",
            message=f"Collected {len(papers)} papers from {category}",
            summary=f"Fetched {len(papers)} paper(s) from arXiv category {category} and saved them to output/papers/.",
            next_step="Open the Library page to read the abstracts and open the saved Markdown.",
            item_count=len(papers),
            saved_paths=[f"output/papers/{category}"],
            extra_details={"category": category, "max_results": max_results},
        )
    if source == "wechat":
        import collect.wechat as wechat_collect

        url = fields.get("url", "")
        if not url:
            return _format_collect_result(
                source="wechat",
                status="error",
                message="WeChat collection requires a URL",
                summary="WeChat collect was called without an article URL.",
                next_step="Switch to the WeChat source, paste a mp.weixin.qq.com article URL into the URL field, and Run now.",
                item_count=0,
                saved_paths=[],
            )
        asyncio.run(wechat_collect.fetch_article(url, output_dir=root / "wechat"))
        return _format_collect_result(
            source="wechat",
            status="success",
            message=f"Collected WeChat article: {url}",
            summary=f"Saved the WeChat article to output/wechat/.",
            next_step="Open the Library page to read the article Markdown.",
            item_count=1,
            saved_paths=["output/wechat/"],
            extra_details={"url": url},
        )
    return _format_collect_result(
        source=source,
        status="error",
        message=f"Unknown source: {source}",
        summary=f"Collect source '{source}' is not supported by this workspace.",
        next_step="Pick one of the supported sources: GitHub, arXiv Papers, or WeChat.",
        item_count=0,
        saved_paths=[],
    )


class PreviewError(Exception):
    """Raised by `read_item_markdown` for any failure that should surface
    to the user as a non-200 response."""


def read_item_markdown(output_root: Path, output_path: str) -> tuple[str, str]:
    """Read a Markdown file from a known ResearchItem sidecar.

    Three guards, in order:
    1. Path must resolve inside `output_root` (no `..` traversal, no absolute escape).
    2. `output_path` MUST be a known sidecar's `output_path` — we never serve
       arbitrary Markdown inside `output_root`.
    3. The underlying file must exist and be readable.

    Returns `(body, content_type)`. Raises `FileNotFoundError` for "not a
    known archive entry" / "file missing" and `PreviewError` for traversal.
    """
    from library.storage import load_research_items

    output_root = Path(output_root).resolve()
    requested = Path(output_path)

    # Guard 1: traversal. The `output_path` stored in sidecars is typically
    # written relative to the PROJECT ROOT (e.g. "output/github/foo/README.md"),
    # not relative to `output_root` itself. Anchor relative paths to
    # `output_root.parent` so they resolve correctly, then verify the
    # resolved candidate is strictly inside `output_root`.
    if requested.is_absolute():
        candidate = requested.resolve()
    else:
        candidate = (output_root.parent / requested).resolve()

    try:
        candidate.relative_to(output_root)
    except ValueError as exc:
        raise PreviewError(
            f"Refusing to read outside output_root: {output_path!r}"
        ) from exc

    # Guard 2: only known sidecar paths are readable. `item.output_path`
    # is relative to the PROJECT ROOT (e.g. "output/github/foo/README.md")
    # but we need to compare it relative to `output_root`. Strip the
    # leading "output" segment so the comparison is apples-to-apples.
    candidate_rel = candidate.relative_to(output_root).as_posix()
    project_root = output_root.parent
    known_paths = set()
    for item in load_research_items(output_root):
        if not item.output_path:
            continue
        # Resolve the known path the same way we resolved `candidate`.
        known_abs = (project_root / item.output_path).resolve()
        try:
            known_rel = known_abs.relative_to(output_root).as_posix()
        except ValueError:
            continue
        if known_rel == candidate_rel:
            known_paths.add(known_rel)
    if candidate_rel not in known_paths:
        raise FileNotFoundError(
            f"Refusing: {output_path!r} is not a known archive entry. "
            f"Only sidecar output_paths are readable."
        )

    # Guard 3: file must exist.
    if not candidate.is_file():
        raise FileNotFoundError(f"Markdown file missing: {output_path!r}")

    body = candidate.read_text(encoding="utf-8", errors="replace")
    return body, "text/markdown; charset=utf-8"