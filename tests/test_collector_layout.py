"""Contract tests: freshly collected items land on the target archive layout.

The refactor's exit criterion is that *new* collection never reproduces a legacy
path, and that a collected item's ``output_path`` is exactly what the migration
planner would compute for the same identity. These tests call the real
collectors (with faked source boundaries) against a temporary output root and
then assert agreement with :func:`library.migration.compute_target`.
"""

from __future__ import annotations

import json
from pathlib import Path

from ai_intel_station.collect import github as github_mod
from ai_intel_station.collect import hackernews as hn_mod
from ai_intel_station.collect import papers as papers_mod
from ai_intel_station.library import migration
from ai_intel_station.library.archive_paths import github_search_leaf, paper_leaf
from ai_intel_station.library.items import write_research_item
from ai_intel_station.library.storage import load_research_items


def _item_output_path(output_root: Path, item) -> Path:
    raw = Path(item.output_path)
    if raw.is_absolute():
        return raw
    if raw.parts and raw.parts[0] == output_root.name:
        return output_root.parent / raw
    return output_root / raw


def _rel_to_root(item, output_root: Path) -> str:
    """Return the item's primary material as a path relative to ``output_root``.

    Collectors store repository-relative paths for the real repo root and absolute
    paths for temp roots; this helper normalizes both to a comparable tail.
    """
    return _item_output_path(output_root, item).relative_to(output_root).as_posix()


def test_save_repo_writes_nested_identity(tmp_path: Path, monkeypatch) -> None:
    out = tmp_path / "output" / "github"
    monkeypatch.setattr(github_mod, "fetch_repo", lambda owner, repo, **kw: {
        "name": "widget", "description": "d", "url": f"https://github.com/{owner}/{repo}",
        "stargazerCount": 1, "primaryLanguage": {"name": "Py"}, "repositoryTopics": [],
        "createdAt": "2026-01-01T00:00:00Z", "updatedAt": "2026-01-01T00:00:00Z", "issues": [],
    })
    path = github_mod.save_repo("octo", "widget", out)
    assert path == out / "octo" / "widget" / "README.md"
    assert path.is_file()
    item = load_research_items(tmp_path / "output")[0]
    assert _rel_to_root(item, tmp_path / "output") == "github/octo/widget/README.md"
    # The migration computes the identical target for this item.
    assert migration.compute_target(item)["markdown"] == "github/octo/widget/README.md"


def test_save_search_results_uses_snapshot_namespace(tmp_path: Path) -> None:
    out = tmp_path / "output" / "github"
    repos = [{"name": "alpha", "url": "https://github.com/a/alpha", "stargazersCount": 1,
              "description": "d", "createdAt": "", "updatedAt": "", "owner": {"login": "a"}}]
    path = github_mod.save_search_results("agent harness", out, repos, collected_at="2026-08-20T10:00:00Z")
    assert "_search" in str(path)
    assert path == out / github_search_leaf("agent harness", "2026-08-20T10:00:00Z") / "search.md"
    # Snapshot results never collide with a repository dir named "agent-harness".
    assert path.parent.parent == out / "_search"


def test_save_papers_flat_by_arxiv_id_merges_categories(tmp_path: Path) -> None:
    out = tmp_path / "output" / "papers"
    paper = {"title": "AutoDesign", "authors": ["X"], "summary": "abs",
             "published": "2026-08-13T00:00:00Z", "updated": "2026-08-13T00:00:00Z",
             "arxiv_id": "2608.13560v1", "pdf_url": "https://arxiv.org/pdf/2608.13560v1",
             "abs_url": "https://arxiv.org/abs/2608.13560v1", "categories": ["cs.AI", "cs.CV", "cs.CL"]}
    papers_mod.save_papers([paper], "cs.AI", out)
    # Cross-category copy from a different category writes the SAME flat path.
    papers_mod.save_papers([dict(paper, categories=["cs.CL"])], "cs.CL", out)
    assert list(out.glob("arXiv-*")) == []  # no legacy category dir
    md = out / paper_leaf("2608.13560v1")
    assert md.is_file()
    items = load_research_items(tmp_path / "output")
    assert len(items) == 1
    assert _rel_to_root(items[0], tmp_path / "output") == "papers/2608.13560v1.md"
    assert set(items[0].tags) >= {"cs.AI", "cs.CV", "cs.CL"}


def test_hn_collect_feed_writes_per_story_units(tmp_path: Path) -> None:
    out = tmp_path / "output" / "hackernews"
    stories = {
        100: {"id": 100, "type": "story", "title": "Alpha", "by": "u", "time": 1756500000,
              "url": "https://x/alpha", "score": 9, "descendants": 2},
        200: {"id": 200, "type": "story", "title": "Beta", "by": "v", "time": 1756500100,
              "url": "https://x/beta", "score": 3, "descendants": 0},
    }

    def fake_request_json(url, **kw):
        if url.endswith("/topstories.json"):
            return [100, 200]
        item_id = int(url.rsplit("/", 1)[-1].split(".")[0])
        return stories[item_id]

    hn_mod.collect_feed("topstories", keywords=[], limit=10, output_dir=out, request_json=fake_request_json)

    assert (out / "100.md").is_file() and (out / "100.research-item.json").is_file()
    assert (out / "200.md").is_file()
    assert not (out / "topstories").exists()  # no legacy feed dir
    items = {i.metadata["item_id"]: i for i in load_research_items(tmp_path / "output")}
    assert _rel_to_root(items[100], tmp_path / "output") == "hackernews/100.md"
    assert items[100].metadata["feed"] == "topstories"
    assert items[100].metadata["rank"] == 1
    # Cross-feed re-collection keeps one unit and accumulates feed provenance.
    hn_mod.collect_feed("beststories", keywords=[], limit=10, output_dir=out,
                        request_json=lambda url, **kw: [100] if url.endswith("beststories.json") else stories[100])
    item = load_research_items(tmp_path / "output")
    assert len([i for i in item if i.metadata.get("item_id") == 100]) == 1
    assert set(next(i for i in item if i.metadata["item_id"] == 100).metadata["feeds"]) >= {"topstories", "beststories"}


def test_collected_paper_matches_migration_target(tmp_path: Path) -> None:
    """A collected item and the migration agree on the physical identity — one rule."""
    out = tmp_path / "output" / "papers"
    papers_mod.save_papers([{
        "title": "Lone", "authors": ["A"], "summary": "s", "published": "2026-01-01T00:00:00Z",
        "updated": "2026-01-01T00:00:00Z", "arxiv_id": "2601.00007v2",
        "pdf_url": "https://arxiv.org/pdf/2601.00007v2", "abs_url": "https://arxiv.org/abs/2601.00007v2",
        "categories": ["cs.LG"],
    }], "cs.LG", out)
    item = load_research_items(tmp_path / "output")[0]
    assert migration.compute_target(item)["markdown"] == "papers/2601.00007v2.md"
    assert item.output_path.endswith("papers/2601.00007v2.md")
