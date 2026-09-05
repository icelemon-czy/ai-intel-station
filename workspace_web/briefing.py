from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from briefing.service import build_generic_briefing, save_generic_briefing


_MODE_PURPOSES = {
    "digest": "Summarize the matching local items into a short digest you can read end-to-end.",
    "reading-list": "Queue the matching local items into a reading list for later review.",
}
_ACTION_PURPOSES = {
    "preview": "Show the derived Markdown in-page only. Does not write any file.",
    "save": "Write the derived Markdown to output/briefing/ as a saved reading artifact.",
}
_FLOW_NOTES = {
    "input_source": "Briefings are generated from the local Library / ResearchItem sidecar only — no remote fetch happens here.",
    "preview_vs_save": "Preview keeps the result in this panel. Save persists a Markdown file to output/briefing/.",
    "saved_artifact": "Saved files are derived reading artifacts, not new primary research items.",
}


def briefing_mode_purposes() -> dict[str, str]:
    return dict(_MODE_PURPOSES)


def briefing_action_purposes() -> dict[str, str]:
    return dict(_ACTION_PURPOSES)


def briefing_flow_notes() -> dict[str, str]:
    return dict(_FLOW_NOTES)


def preview_briefing(
    output_root: Path,
    mode: str,
    keyword: str,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> dict[str, object]:
    briefing = build_generic_briefing(
        output_root,
        mode=mode,
        keyword=keyword,
        title=title,
        sources=sources,
        since=since,
        until=until,
    )
    result: dict[str, object] = {
        "title": briefing.title,
        "mode": briefing.mode,
        "content": briefing.content,
        "item_count": len(briefing.items),
    }
    if not briefing.items:
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
    saved = save_generic_briefing(
        build_generic_briefing(
            output_root,
            mode=mode,
            keyword=keyword,
            title=title,
            sources=sources,
            since=since,
            until=until,
        ),
        output_root,
    )
    assert saved.path is not None
    return {
        "title": saved.title,
        "mode": saved.mode,
        "path": saved.path.as_posix(),
        "content": saved.content,
        "saved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
