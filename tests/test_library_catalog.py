from __future__ import annotations

from pathlib import Path

from library.catalog import build_library_catalog
from library.items import ResearchItem, write_research_item


def _seed_item(output_root: Path, relative: str, item: ResearchItem) -> Path:
    markdown = output_root / relative
    markdown.parent.mkdir(parents=True, exist_ok=True)
    markdown.write_text(f"# {item.title}\n", encoding="utf-8")
    item.output_path = f"output/{relative}"
    sidecar = markdown.with_name(f"{markdown.stem}.research-item.json")
    write_research_item(item, sidecar)
    return markdown


def test_catalog_adds_date_tag_and_duplicate_views_without_moving_archive(tmp_path: Path) -> None:
    output_root = tmp_path / "output"
    first = _seed_item(
        output_root,
        "papers/cs.AI/first.md",
        ResearchItem(
            source="papers",
            item_type="paper",
            title="First Paper",
            canonical_url="https://example.com/shared",
            published_at="2026-08-20",
            tags=["cs.AI", "agents"],
        ),
    )
    second = _seed_item(
        output_root,
        "papers/cs.CL/second.md",
        ResearchItem(
            source="papers",
            item_type="paper",
            title="First Paper in another category",
            canonical_url="https://example.com/shared",
            published_at="2026-08-20",
            tags=["cs.CL", "agents"],
        ),
    )
    third = _seed_item(
        output_root,
        "github/demo/README.md",
        ResearchItem(
            source="github",
            item_type="repository",
            title="Untagged Repository",
            canonical_url="https://github.com/example/demo",
        ),
    )
    orphan = output_root / "github" / "legacy-search.md"
    orphan.write_text("# Search: agent\n\nFound 0 repositories\n", encoding="utf-8")
    originals = {path: path.read_bytes() for path in (first, second, third)}

    catalog = build_library_catalog(output_root)

    assert catalog.item_count == 3
    assert catalog.tag_count == 3
    assert catalog.untagged_count == 1
    assert catalog.undated_count == 1
    assert catalog.duplicate_groups == 1
    assert catalog.orphan_markdown_count == 1
    assert {path.name for path in catalog.paths} == {
        "index.md",
        "by-date.md",
        "by-tag.md",
        "duplicates.md",
        "orphans.md",
    }
    assert originals == {path: path.read_bytes() for path in originals}
    assert first.exists() and second.exists() and third.exists()

    by_date = (output_root / "briefing" / "library" / "by-date.md").read_text()
    by_tag = (output_root / "briefing" / "library" / "by-tag.md").read_text()
    duplicates = (output_root / "briefing" / "library" / "duplicates.md").read_text()
    assert "## 2026-08" in by_date
    assert "## Unknown date" in by_date
    assert "## agents (2)" in by_tag
    assert "## Untagged (1)" in by_tag
    assert "https://example.com/shared" in duplicates
    assert "../../papers/cs.AI/first.md" in by_date
    orphans = (output_root / "briefing" / "library" / "orphans.md").read_text()
    assert "github/legacy-search.md" in orphans


def test_organize_cli_rebuilds_stable_catalog_paths(tmp_path: Path, capsys) -> None:
    from research.cli import main

    output_root = tmp_path / "output"
    _seed_item(
        output_root,
        "github/demo/README.md",
        ResearchItem(
            source="github",
            item_type="repository",
            title="Demo",
            canonical_url="https://github.com/example/demo",
            updated_at="2026-08-29",
        ),
    )

    assert main(["organize", "--output-root", str(output_root)]) == 0
    assert main(["organize", "--output-root", str(output_root)]) == 0

    rendered = capsys.readouterr().out
    assert "without moving primary archive" in rendered
    catalog_dir = output_root / "briefing" / "library"
    assert sorted(path.name for path in catalog_dir.glob("*.md")) == [
        "by-date.md",
        "by-tag.md",
        "duplicates.md",
        "index.md",
        "orphans.md",
    ]


def test_catalog_is_not_reported_as_recent_briefing(tmp_path: Path) -> None:
    from workspace_web.dashboard import build_dashboard_overview

    output_root = tmp_path / "output"
    _seed_item(
        output_root,
        "github/demo/README.md",
        ResearchItem(
            source="github",
            item_type="repository",
            title="Demo",
            canonical_url="https://github.com/example/demo",
            updated_at="2026-08-29",
        ),
    )
    build_library_catalog(output_root)

    overview = build_dashboard_overview(output_root)

    assert overview["recent_briefings"] == []
