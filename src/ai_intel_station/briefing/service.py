from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai_intel_station.library.items import ResearchItem
from ai_intel_station.library.service import search_library
from ai_intel_station.briefing.markdown import briefing_output_path, write_markdown

from .reports import build_digest_markdown, build_reading_list_markdown


@dataclass(frozen=True)
class GenericBriefing:
    title: str
    mode: str
    content: str
    items: tuple[ResearchItem, ...]
    path: Path | None = None


def build_generic_briefing(
    output_root: Path,
    *,
    mode: str,
    keyword: str,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> GenericBriefing:
    if mode not in {"digest", "reading-list"}:
        raise ValueError(f"unsupported briefing mode: {mode}")
    items = search_library(
        output_root,
        keyword=keyword,
        sources=sources,
        since=since,
        until=until,
    )
    return build_generic_briefing_from_items(
        mode=mode,
        title=title or keyword,
        items=items,
        requested_sources=sources,
    )


def build_generic_briefing_from_items(
    *,
    mode: str,
    title: str,
    items: list[ResearchItem],
    requested_sources: list[str] | None = None,
) -> GenericBriefing:
    if mode not in {"digest", "reading-list"}:
        raise ValueError(f"unsupported briefing mode: {mode}")
    builder = build_digest_markdown if mode == "digest" else build_reading_list_markdown
    content = builder(title, items, requested_sources=requested_sources)
    return GenericBriefing(
        title=title,
        mode=mode,
        content=content,
        items=tuple(items),
    )


def save_generic_briefing(briefing: GenericBriefing, output_root: Path) -> GenericBriefing:
    section = "digests" if briefing.mode == "digest" else "reading-lists"
    path = briefing_output_path(output_root, section, briefing.title)
    write_markdown(path, briefing.content)
    return GenericBriefing(
        title=briefing.title,
        mode=briefing.mode,
        content=briefing.content,
        items=briefing.items,
        path=path,
    )
