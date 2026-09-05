"""Contract tests for the shared archive migration service.

These exercise the real on-disk boundary (write sidecars + markdown, run the
planner, apply atomically, re-read through the Library loader) inside a
temporary output root — never the repository archive. They cover the seven
behaviors the refactor requires as a contract:

- dry-run plans without writing
- idempotency (apply twice == apply once)
- collision detection (non-equivalent copies are never deleted)
- rollback boundary (verified backup restores the archive byte-for-byte)
- sidecar ``output_path`` rewritten to the existing target
- WeChat relative image links keep resolving after the move
- cross-category / cross-feed provenance is preserved through a merge
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from ai_intel_station.library import migration
from ai_intel_station.library.items import ResearchItem, utc_now_iso
from ai_intel_station.library.storage import load_research_items


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _arxiv_sidecar(identity: str, url: str, title: str, tags: list[str], out: str,
                   discovered: str = "2026-08-15T00:00:00Z") -> dict:
    return ResearchItem(
        source="papers", item_type="paper", title=title, canonical_url=url,
        published_at="2026-08-10T00:00:00Z", discovered_at=discovered,
        signal_role="evidence", discovery_method="arxiv-category",
        tags=tags, output_path=out, metadata={"pdf_url": url.replace("/abs/", "/pdf/")},
    ).to_dict()


@pytest.fixture()
def legacy_archive(tmp_path: Path) -> Path:
    """Build a small archive that mirrors every legacy layout in the repo."""
    out = tmp_path / "output"

    # GitHub repository (flattened owner-repo dir).
    repo = out / "github" / "octo-widget"
    repo.mkdir(parents=True)
    (repo / "README.md").write_text("# widget\n\n> A widget.\n\n- 🌐 URL: https://github.com/octo/widget\n", encoding="utf-8")
    _write_json(repo / "research-item.json", ResearchItem(
        source="github", item_type="repository", title="widget",
        canonical_url="https://github.com/octo/widget", signal_role="evidence",
        discovery_method="github-repository", output_path="output/github/octo-widget/README.md",
        metadata={"owner": "octo", "repo": "widget"},
    ).to_dict())

    # GitHub search snapshot (query dir, shared batch jsonl).
    search = out / "github" / "agent-harness"
    search.mkdir(parents=True)
    (search / "search.md").write_text("# Search: agent harness\n\nFound 2 repositories\n\n## [alpha](https://github.com/a/alpha)\n", encoding="utf-8")
    (search / "research-items.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in [
        {"source": "github", "item_type": "search-result", "title": "alpha",
         "canonical_url": "https://github.com/a/alpha", "discovered_at": "2026-08-20T00:00:00Z",
         "output_path": "output/github/agent-harness/search.md",
         "metadata": {"query": "agent harness", "owner": "a", "repo": "alpha"}},
        {"source": "github", "item_type": "search-result", "title": "beta",
         "canonical_url": "https://github.com/b/beta", "discovered_at": "2026-08-20T00:00:00Z",
         "output_path": "output/github/agent-harness/search.md",
         "metadata": {"query": "agent harness", "owner": "b", "repo": "beta"}},
    ]) + "\n", encoding="utf-8")

    # arXiv cross-category duplicates (byte-identical markdown → provable merge).
    md_body = "# AutoDesign\n\n> **Authors:** X\n\n- 🔗 arXiv: https://arxiv.org/abs/2608.13560v1\n\n## Abstract\n\nHello.\n"
    for cat in ("cs.AI", "cs.CL"):
        stem = f"01-AutoDesign.{cat}"
        pdf = out / "papers" / f"arXiv-{cat}"
        pdf.mkdir(parents=True, exist_ok=True)
        (pdf / f"01-AutoDesign-{cat}.md").write_text(md_body, encoding="utf-8")
        _write_json(pdf / f"01-AutoDesign-{cat}.research-item.json",
                    _arxiv_sidecar("2608.13560v1", "https://arxiv.org/abs/2608.13560v1",
                                   "AutoDesign", ["cs.CV", "cs.AI", "cs.CL"] if cat == "cs.AI" else ["cs.CL"],
                                   f"output/papers/arXiv-{cat}/01-AutoDesign-{cat}.md"))

    # A lone paper that stays a single unit.
    single = out / "papers" / "arXiv-cs.LG"
    single.mkdir(parents=True, exist_ok=True)
    (single / "02-Lone.md").write_text("# Lone\n\n- 🔗 arXiv: https://arxiv.org/abs/2608.00002v1\n", encoding="utf-8")
    _write_json(single / "02-Lone.research-item.json",
                _arxiv_sidecar("2608.00002v1", "https://arxiv.org/abs/2608.00002v1", "Lone", ["cs.LG"],
                               "output/papers/arXiv-cs.LG/02-Lone.md"))

    # WeChat article with a relative image link (whole dir moves as one unit).
    art = out / "wechat" / "刚刚一篇综述"
    (art / "images").mkdir(parents=True)
    (art / "images" / "img_001.png").write_bytes(b"\x89PNG fake")
    (art / "刚刚一篇综述.md").write_text(
        "# 刚刚一篇综述\n\n> 发布时间: 2026-05-27 23:58:30\n> 原文链接: https://mp.weixin.qq.com/s/AAA111\n\n"
        "---\n\n![cover](images/img_001.png)\n", encoding="utf-8")
    _write_json(art / "research-item.json", ResearchItem(
        source="wechat", item_type="article", title="刚刚一篇综述",
        canonical_url="https://mp.weixin.qq.com/s/AAA111", published_at="2026-05-27 23:58:30",
        discovered_at=utc_now_iso(), signal_role="signal",
        output_path="output/wechat/刚刚一篇综述/刚刚一篇综述.md", metadata={"publisher": "Datawhale"},
    ).to_dict())

    # Hacker News: two feed batch files, one story shared across both feeds.
    shared = {"source": "hackernews", "item_type": "story", "title": "Shared Story",
              "canonical_url": "https://example.com/shared", "published_at": "2026-08-29T07:00:00Z",
              "discovered_at": "2026-08-29T08:00:00Z", "signal_role": "signal"}
    only_new = dict(shared, title="NewOnly", canonical_url="https://example.com/new",
                    metadata={"feed": "newstories", "item_id": 111, "discussion_url": "https://news.ycombinator.com/item?id=111", "score": 5})
    lines_new = [
        json.dumps({**shared, "metadata": {"feed": "newstories", "item_id": 42,
                    "discussion_url": "https://news.ycombinator.com/item?id=42", "score": 1},
                    "discovery_method": "hackernews-newstories",
                    "output_path": "output/hackernews/newstories/signals.md"}, ensure_ascii=False),
        json.dumps({**only_new, "discovery_method": "hackernews-newstories",
                    "output_path": "output/hackernews/newstories/signals.md"}, ensure_ascii=False),
    ]
    lines_show = [
        json.dumps({**shared, "metadata": {"feed": "showstories", "item_id": 42,
                    "discussion_url": "https://news.ycombinator.com/item?id=42", "score": 2},
                    "discovery_method": "hackernews-showstories",
                    "output_path": "output/hackernews/showstories/signals.md"}, ensure_ascii=False),
    ]
    for feed, lines in (("newstories", lines_new), ("showstories", lines_show)):
        d = out / "hackernews" / feed
        d.mkdir(parents=True)
        (d / "signals.md").write_text(f"# Hacker News: {feed}\n\n## [Shared Story](https://example.com/shared)\n", encoding="utf-8")
        (d / "research-items.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Orphan: an empty search run artifact at the github root.
    (out / "github").mkdir(exist_ok=True)
    (out / "github" / "search.md").write_text("# Search: agent\n\nFound 0 repositories\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------- #
# dry-run                                                                     #
# --------------------------------------------------------------------------- #

def test_dry_run_plans_without_writing(legacy_archive: Path) -> None:
    before = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    plan = migration.plan_migration(legacy_archive)

    # Nothing on disk changed during planning.
    after = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    assert before == after

    # The paper merge is recognized: two identical copies -> one proven-equivalent group.
    merge_identities = {(m["source"], m["identity"]) for m in plan.merges}
    assert ("papers", "2608.13560v1") in merge_identities
    assert all(m["equivalent"] for m in plan.merges)

    # Cross-feed HN story collapses into a single materialized unit by identity.
    hn_units = [u for u in plan.units if u["source"] == "hackernews"]
    identities = sorted(u["identity"] for u in hn_units)
    assert identities == ["111", "42"], identities

    # Orphan: empty search.md is an approved delete; nothing else is a stray orphan.
    assert any("search.md" == Path(o["path"]).name for o in plan.delete_orphans)

    # GitHub search snapshot relocates to the _search namespace.
    assert any("_search" in u["target_markdown"] for u in plan.units if u["source"] == "github")


# --------------------------------------------------------------------------- #
# apply + sidecar path + images                                               #
# --------------------------------------------------------------------------- #

def test_apply_rewrites_sidecar_paths_and_preserves_images(legacy_archive: Path) -> None:
    backup = legacy_archive.parent / "backup"
    result = migration.create_backup(legacy_archive, backup)
    assert migration.verify_backup(legacy_archive, result)

    applied = migration.apply_migration(legacy_archive, require_verified_backup=backup)
    assert applied.errors == [], applied.errors

    items = load_research_items(legacy_archive)
    # No legacy category dir survives.
    assert not list(legacy_archive.glob("papers/arXiv-*"))
    # Every output_path resolves to an existing file.
    for item in items:
        md = legacy_archive.parent / item.output_path if item.output_path.startswith("output") else legacy_archive / item.output_path
        assert md.is_file(), f"dangling output_path {item.output_path}"

    # arXiv merged to a single file keyed by arxiv-id; both categories retained in tags.
    merged = [i for i in items if i.canonical_url == "https://arxiv.org/abs/2608.13560v1"]
    assert len(merged) == 1
    assert set(merged[0].tags) >= {"cs.CV", "cs.AI", "cs.CL"}
    assert merged[0].output_path == "output/papers/2608.13560v1.md"

    # GitHub repository nested identity.
    repo_items = [i for i in items if i.source == "github" and i.item_type == "repository"]
    assert repo_items[0].output_path == "output/github/octo/widget/README.md"
    assert (legacy_archive / "github" / "octo" / "widget" / "README.md").is_file()

    # WeChat unit moved with images; the relative link still resolves.
    wx = next(i for i in items if i.source == "wechat")
    assert wx.output_path.startswith("output/wechat/2026-05-27-")
    md_abs = legacy_archive / Path(wx.output_path).relative_to("output")
    text = md_abs.read_text(encoding="utf-8")
    assert "images/img_001.png" in text
    assert (md_abs.parent / "images" / "img_001.png").is_file()


def test_hn_merge_preserves_feed_provenance(legacy_archive: Path) -> None:
    backup = legacy_archive.parent / "backup-hn"
    migration.create_backup(legacy_archive, backup)
    migration.apply_migration(legacy_archive, require_verified_backup=backup)
    items = load_research_items(legacy_archive)
    shared = next(i for i in items if i.canonical_url == "https://example.com/shared")
    assert shared.output_path == "output/hackernews/42.md"
    assert set(shared.metadata.get("feeds", [])) == {"newstories", "showstories"}
    assert (legacy_archive / "hackernews" / "42.md").is_file()
    # The legacy per-feed batch dirs are gone.
    assert not (legacy_archive / "hackernews" / "newstories").exists()


# --------------------------------------------------------------------------- #
# idempotency                                                                 #
# --------------------------------------------------------------------------- #

def test_migration_is_idempotent(legacy_archive: Path) -> None:
    backup = legacy_archive.parent / "backup-idem"
    migration.create_backup(legacy_archive, backup)
    migration.apply_migration(legacy_archive, require_verified_backup=backup)
    first = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}

    second_plan = migration.plan_migration(legacy_archive)
    # After the first apply there should be no pending moves/merges/splits, only noops.
    assert second_plan.merges == []
    assert second_plan.delete_orphans == []
    active = [u for u in second_plan.units if u["kind"] != "noop"]
    assert active == [], active

    # A second apply must re-verify a *fresh* boundary describing the migrated
    # tree (the pre-migration boundary is now stale), and must change nothing.
    backup2 = legacy_archive.parent / "backup-idem-2"
    migration.create_backup(legacy_archive, backup2)
    migration.apply_migration(legacy_archive, require_verified_backup=backup2)
    second = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    assert first == second


def test_apply_requires_verified_backup(legacy_archive: Path) -> None:
    """The public mutation API must refuse to bulk-mutate without a boundary."""
    before = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    with pytest.raises((RuntimeError, TypeError)):
        migration.apply_migration(legacy_archive)  # type: ignore[call-arg]
    after = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    assert before == after


# --------------------------------------------------------------------------- #
# collision safety                                                            #
# --------------------------------------------------------------------------- #

def test_conflicting_copies_are_not_merged_or_deleted(tmp_path: Path) -> None:
    out = tmp_path / "output"
    url = "https://arxiv.org/abs/2609.00009v1"
    for cat, body in (("cs.AI", "# Same Title\n\nAbstract A\n"), ("cs.CL", "# Same Title\n\nAbstract B DIFFERENT\n")):
        d = out / "papers" / f"arXiv-{cat}"
        d.mkdir(parents=True)
        (d / f"01-X-{cat}.md").write_text(body, encoding="utf-8")
        _write_json(d / f"01-X-{cat}.research-item.json",
                    _arxiv_sidecar("2609.00009v1", url, "Same Title", [cat],
                                   f"output/papers/arXiv-{cat}/01-X-{cat}.md"))
    plan = migration.plan_migration(out)
    assert len(plan.collisions) == 1
    assert plan.collisions[0]["equivalent"] is False
    assert plan.merges == []

    backup = tmp_path / "backup-collision"
    migration.create_backup(out, backup)
    migration.apply_migration(out, require_verified_backup=backup)
    # Both conflicting source files are still present — nothing was deleted.
    assert (out / "papers" / "arXiv-cs.AI" / "01-X-cs.AI.md").is_file()
    assert (out / "papers" / "arXiv-cs.CL" / "01-X-cs.CL.md").is_file()


# --------------------------------------------------------------------------- #
# rollback                                                                    #
# --------------------------------------------------------------------------- #

def test_rollback_restores_archive(legacy_archive: Path) -> None:
    original = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    backup = legacy_archive.parent / "backup"
    result = migration.create_backup(legacy_archive, backup)
    assert migration.verify_backup(legacy_archive, result)

    migration.apply_migration(legacy_archive, require_verified_backup=backup)
    migrated = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    assert migrated != original

    migration.rollback(legacy_archive, result)
    restored = {p.relative_to(legacy_archive).as_posix(): _sha(p) for p in legacy_archive.rglob("*") if p.is_file()}
    assert restored == original


def test_apply_refuses_stale_backup(legacy_archive: Path) -> None:
    backup = legacy_archive.parent / "backup"
    migration.create_backup(legacy_archive, backup)
    # Mutate the archive after backup so the boundary is no longer valid.
    (legacy_archive / "papers" / "injected.md").write_text("# injected\n", encoding="utf-8")
    with pytest.raises(RuntimeError):
        migration.apply_migration(legacy_archive, require_verified_backup=backup)


# --------------------------------------------------------------------------- #
# manifest                                                                    #
# --------------------------------------------------------------------------- #

def test_manifest_records_hash_identity_and_image_links(legacy_archive: Path) -> None:
    manifest = migration.build_migration_manifest(legacy_archive)
    assert manifest["schema"] == "ai-intel-station/archive-migration-manifest/v1"
    paths = {f["path"] for f in manifest["files"]}
    assert any(f["sha256"] for f in manifest["files"])
    assert any("git_status" in f for f in manifest["files"])

    by_identity = {(s["source"], s["identity"]): s for s in manifest["sidecars"]}
    wx = by_identity[("wechat", "https://mp.weixin.qq.com/s/AAA111")]
    assert wx["relative_image_links"] == ["images/img_001.png"]
    assert wx["target_markdown"].startswith("output/wechat/2026-05-27-")
    paper = by_identity[("papers", "2608.13560v1")]
    assert paper["canonical_url"] == "https://arxiv.org/abs/2608.13560v1"


# --------------------------------------------------------------------------- #
# backup topology safety (no destructive overlap)                             #
# --------------------------------------------------------------------------- #

def _tree(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): _sha(p) for p in root.rglob("*") if p.is_file()}


def test_backup_rejects_backup_dir_equal_to_output_parent(legacy_archive: Path) -> None:
    # backup_dir == output_root.parent would make target_output == output_root,
    # and the rmtree(target_output) would delete the live archive.
    before = _tree(legacy_archive)
    with pytest.raises(ValueError):
        migration.create_backup(legacy_archive, legacy_archive.parent)
    assert _tree(legacy_archive) == before


def test_backup_rejects_backup_dir_inside_output_root(legacy_archive: Path) -> None:
    before = _tree(legacy_archive)
    with pytest.raises(ValueError):
        migration.create_backup(legacy_archive, legacy_archive / "nested-backup")
    assert _tree(legacy_archive) == before


def test_backup_rejects_backup_dir_equal_to_output_root(legacy_archive: Path) -> None:
    before = _tree(legacy_archive)
    with pytest.raises(ValueError):
        migration.create_backup(legacy_archive, legacy_archive)
    assert _tree(legacy_archive) == before


def test_backup_allows_safe_sibling_dir(legacy_archive: Path) -> None:
    # A sibling directory (and the tree it produces) does not touch the archive,
    # so it must NOT be rejected — the guard targets destructive overlap only.
    before = _tree(legacy_archive)
    sibling = legacy_archive.parent / "safe-backup"
    result = migration.create_backup(legacy_archive, sibling)
    assert migration.verify_backup(legacy_archive, result)
    assert _tree(legacy_archive) == before  # creating a backup never mutates the archive


def test_rollback_rejects_destructive_topology(tmp_path: Path) -> None:
    out = tmp_path / "output"
    (out / "papers").mkdir(parents=True)
    (out / "papers" / "keep.md").write_text("# keep\n", encoding="utf-8")
    # Fabricate a backup object that claims the backup tree overlaps the archive.
    fake = migration.BackupResult(backup_dir=out.parent, manifest_path=out.parent / "manifest.json",
                                  file_count=0, combined_sha256="")
    before = _tree(out)
    with pytest.raises(ValueError):
        migration.rollback(out, fake)
    assert _tree(out) == before
