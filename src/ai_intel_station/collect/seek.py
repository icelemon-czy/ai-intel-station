"""Interest Sweep: one topic keyword sweep across GitHub, arXiv and Hacker News.

Design: doc/interest_sweep_design.md. This orchestration deliberately does not
import ``ai_intel_station.discovery`` — a seek is a stateless one-off topic pull,
not the configured daily loop. It also never generates briefing: the CLI composes
the this-run reading list from the returned items via ``briefing.service``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ai_intel_station.collect import github, hackernews, papers
from ai_intel_station.collect.service import GITHUB_SEARCH_FIELDS
from ai_intel_station.library.archive_paths import arxiv_identity, paper_leaf
from ai_intel_station.library.items import (
    ResearchItem,
    build_github_search_items,
    build_paper_item,
)
from ai_intel_station.library.storage import load_research_items


SEEK_FEEDS = ["newstories", "showstories"]
SEEK_SOURCES = ("github", "papers", "hackernews")


@dataclass
class SourceStatus:
    new_count: int = 0
    skipped_count: int = 0
    failed: bool = False


@dataclass
class SeekResult:
    topic: str
    dry_run: bool
    new_items: list[ResearchItem] = field(default_factory=list)
    existing_items: list[ResearchItem] = field(default_factory=list)
    sources: dict[str, SourceStatus] = field(default_factory=dict)
    briefing_path: Path | None = None
    message: str = ""

    @property
    def failures(self) -> tuple[str, ...]:
        """Failed source names, derived from the per-source statuses."""
        return tuple(name for name, status in self.sources.items() if status.failed)


def _dry_run_message(topic: str, limit: int) -> str:
    return "\n".join(
        [
            f"Seek plan for {topic!r} (dry-run, no network, no writes):",
            f"  GitHub: gh search repos {topic} --sort updated --limit {limit}",
            f'  arXiv: search_query=all:"{topic}" --limit {limit}',
            f"  Hacker News: feeds {'+'.join(SEEK_FEEDS)} keyword={topic} --limit {limit}",
        ]
    )


def format_seek_report(result: SeekResult) -> str:
    if result.dry_run:
        return result.message
    lines = [
        f"Seek {result.topic!r}: {len(result.new_items)} new, "
        f"{len(result.existing_items)} already_in_library",
    ]
    for name in SEEK_SOURCES:
        status = result.sources.get(name)
        if status is None:
            continue
        if status.failed:
            lines.append(f"  {name}: failed")
        else:
            lines.append(
                f"  {name}: {status.new_count} succeeded, {status.skipped_count} skipped"
            )
    lines.append(
        f"  briefing: {result.briefing_path}" if result.briefing_path else "  briefing: skipped"
    )
    return "\n".join(lines)


def run_seek(
    topic: str,
    output_root: Path,
    *,
    dry_run: bool = False,
    limit: int = 10,
) -> SeekResult:
    """Sweep GitHub, arXiv and Hacker News for ``topic`` and persist new hits.

    A URL already present in the local Library is skipped, not re-collected.
    Each source is isolated: one source raising never blocks the others or
    discards artifacts they already saved. No briefing is written here — the
    CLI composes the this-run reading list from ``new_items + existing_items``.
    """
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("topic is required")
    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    root = Path(output_root)

    if dry_run:
        return SeekResult(
            topic=topic,
            dry_run=True,
            message=_dry_run_message(topic, limit),
        )

    known = {
        item.canonical_url: item
        for item in load_research_items(root)
        if item.canonical_url
    }
    new_items: list[ResearchItem] = []
    existing_items: list[ResearchItem] = []
    statuses = {name: SourceStatus() for name in SEEK_SOURCES}

    try:
        raw = github.run_gh(
            [
                "search",
                "repos",
                topic,
                "--sort",
                "updated",
                "--limit",
                str(limit),
                "--json",
                GITHUB_SEARCH_FIELDS,
            ]
        )
        repos = json.loads(raw) if raw.strip() else []
        fresh: list[dict] = []
        for repo in repos:
            url = repo.get("url")
            if url and url in known:
                existing_items.append(known[url])
                statuses["github"].skipped_count += 1
            elif url:
                fresh.append(repo)
        if fresh:
            search_path = github.save_search_results(topic, root / "github", fresh)
            items = build_github_search_items(topic, fresh, search_path)
            new_items.extend(items)
            statuses["github"].new_count += len(items)
    except Exception:  # external source boundary: isolate per-source failure
        statuses["github"].failed = True

    try:
        fetched = papers.fetch_papers_by_query(topic, max_results=limit, raise_on_error=True)
        fresh_papers: list[dict] = []
        for paper in fetched:
            abs_url = paper.get("abs_url")
            if abs_url and abs_url in known:
                existing_items.append(known[abs_url])
                statuses["papers"].skipped_count += 1
            else:
                fresh_papers.append(paper)
        if fresh_papers:
            papers_dir = root / "papers"
            papers.save_papers(fresh_papers, "search", papers_dir)
            for index, paper in enumerate(fresh_papers, start=1):
                title = paper.get("title") or f"untitled-{index:02d}"
                filepath = papers_dir / paper_leaf(
                    arxiv_identity(paper.get("abs_url"), title)
                )
                new_items.append(build_paper_item(paper, filepath))
            statuses["papers"].new_count += len(fresh_papers)
    except Exception:  # external source boundary: isolate per-source failure
        statuses["papers"].failed = True

    try:
        hn_new, hn_existing = hackernews.collect_topic(
            topic,
            feeds=list(SEEK_FEEDS),
            limit=limit,
            output_dir=root / "hackernews",
            known_urls=set(known),
        )
        new_items.extend(hn_new)
        existing_items.extend(hn_existing)
        statuses["hackernews"].new_count += len(hn_new)
        statuses["hackernews"].skipped_count += len(hn_existing)
    except Exception:  # external source boundary: isolate per-source failure
        statuses["hackernews"].failed = True

    result = SeekResult(
        topic=topic,
        dry_run=False,
        new_items=new_items,
        existing_items=existing_items,
        sources=statuses,
    )
    result.message = format_seek_report(result)
    return result
