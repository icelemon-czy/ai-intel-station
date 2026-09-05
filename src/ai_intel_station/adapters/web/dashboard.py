from __future__ import annotations

from pathlib import Path

from ai_intel_station.library.service import display_archive_path
from ai_intel_station.library.storage import load_research_items


SUPPORTED_SOURCES = ("github", "papers", "wechat")


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
    return sorted(
        relative
        for path in output_root.glob("**/*.md")
        if "briefing" not in path.parts
        if (relative := display_archive_path(path, output_root)) not in known_paths
    )


def _recent_briefings(output_root: Path, limit: int = 5) -> list[dict[str, str]]:
    briefing_root = Path(output_root) / "briefing"
    if not briefing_root.exists():
        return []
    paths = sorted(
        (
            path
            for path in briefing_root.glob("**/*.md")
            if path.parent.name != "library"
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    return [
        {
            "title": path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip() or path.stem,
            "path": display_archive_path(path, output_root),
            "section": path.parent.name,
        }
        for path in paths[:limit]
    ]


def build_dashboard_overview(output_root: Path) -> dict[str, object]:
    output_root = Path(output_root)
    items = load_research_items(output_root)
    source_counts = _source_counts(output_root)
    overview: dict[str, object] = {
        "total_items": len(items),
        "source_counts": source_counts,
        "missing_sources": [
            source for source in SUPPORTED_SOURCES if source_counts.get(source, 0) == 0
        ],
        "orphan_markdown_paths": _orphan_markdown_paths(output_root),
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
