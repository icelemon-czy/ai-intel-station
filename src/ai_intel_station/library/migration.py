"""Archive migration service: manifest, rollback boundary, planner and apply.

This is the *single* owner of the physical ``output/`` reorganization rules. The
``research migrate`` CLI (and any future Web action) call these functions; they
never re-implement move/merge logic themselves. The organization rule itself
lives in :mod:`library.archive_paths`, which both this module and the collectors
import, so a freshly collected item and a migrated historical item always land in
the same place.

Guarantees enforced here:

- **Manifest first.** :func:`build_migration_manifest` captures every file hash,
  sidecar identity, canonical URL, output path, relative image link and Git
  status *before* any mutation.
- **Recoverable rollback boundary.** :func:`create_backup` copies the whole
  archive and :func:`verify_backup` proves it is content-complete;
  :func:`rollback` restores it. Any bulk move/delete requires a verified backup.
- **Dry-run planner.** :func:`plan_migration` returns the full old→target map,
  merge groups, splits, collisions, orphans and unresolved conflicts without
  writing anything.
- **Atomic, idempotent apply.** Targets are materialized through temp+fsync+
  rename, then only *superseded* legacy paths (recorded in the plan) are removed.
  Re-running on an already-migrated archive is a no-op.
- **Provenance preservation.** Merging duplicate copies happens only when the
  canonical identity *and* content equivalence are proven; category / feed /
  query / rank provenance is unioned into the surviving sidecar. Conflicting
  copies are reported as collisions and left in place — never silently deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from ai_intel_station.library.archive_paths import (
    SOURCE_DIRS,
    arxiv_identity,
    github_repo_paths,
    github_search_dir,
    hackernews_paths,
    paper_paths,
    wechat_index_leaf,
    wechat_unit_paths,
    x_paths,
)
from ai_intel_station.library.items import (
    ResearchItem,
    _normalize_output_path,
    hackernews_story_markdown,
    utc_now_iso,
    x_post_markdown,
)
from ai_intel_station.library.storage import iter_research_item_sidecars

REPO_ROOT = Path(__file__).resolve().parents[3]

# Derived artifacts are rebuilt separately and are never primary archive material.
PRESERVED_TOPDIRS = {"briefing"}

_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((images/[^)]+)\)")
_VALID_ITEM_FIELDS = {f for f in ResearchItem.__dataclass_fields__}


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return None


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


def _rel(output_root: Path, path: Path) -> str:
    try:
        return PurePosixPath(path.resolve().relative_to(output_root.resolve())).as_posix()
    except ValueError:
        return PurePosixPath(Path(path).as_posix()).as_posix()


def _resolve(output_root: Path, rel_path: str | None) -> Path | None:
    if not rel_path:
        return None
    raw = Path(rel_path)
    if raw.is_absolute():
        return raw
    if raw.parts and raw.parts[0] == output_root.name:
        return output_root.parent / raw
    return output_root / raw


def _stored_output_path(output_root: Path, rel: str | None) -> str | None:
    """Convert an output-root-relative path to the stored ``output_path`` form.

    Collectors persist ``output_path`` repository-relative (e.g.
    ``output/github/octo/widget/README.md``) via :func:`_normalize_output_path`.
    The migration must emit the same convention so a migrated archive is
    indistinguishable from a freshly collected one. For a custom/temp output
    root that is not under ``REPO_ROOT``, fall back to ``<rootname>/<rel>`` so
    :func:`_resolve` keeps resolving it.
    """
    if not rel:
        return None
    absolute = (output_root / rel).resolve()
    normalized = _normalize_output_path(absolute)
    if normalized == absolute.as_posix():  # still absolute -> not under REPO_ROOT
        return (Path(output_root.name) / rel).as_posix()
    return normalized


def _item_from_payload(payload: dict) -> ResearchItem | None:
    if not isinstance(payload, dict):
        return None
    try:
        return ResearchItem(**{k: v for k, v in payload.items() if k in _VALID_ITEM_FIELDS})
    except (TypeError, ValueError):
        return None


def _iter_sidecar_payloads(sidecar_path: Path):
    if sidecar_path.name == "research-items.jsonl":
        try:
            for raw in sidecar_path.read_text(encoding="utf-8-sig").splitlines():
                stripped = raw.strip()
                if not stripped:
                    continue
                try:
                    yield json.loads(stripped)
                except json.JSONDecodeError:
                    continue
        except (OSError, UnicodeDecodeError):
            return
    else:
        try:
            yield json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return


def _load_git_status(output_root: Path) -> dict[str, str]:
    def _run(*args: str) -> list[str]:
        try:
            return subprocess.run(["git", *args], capture_output=True, text=True,
                                  cwd=REPO_ROOT).stdout.splitlines()
        except (OSError, subprocess.SubprocessError):
            return []

    tracked = _run("ls-files", "--", str(output_root))
    status: dict[str, str] = {line[3:].strip().strip('"'): line[:2].strip() or "?"
                              for line in _run("status", "--porcelain", "--", str(output_root))}
    for path in tracked:
        status.setdefault(path, "tracked")
    return status


# --------------------------------------------------------------------------- #
# Identity helpers                                                            #
# --------------------------------------------------------------------------- #

def _gh_url_owner_repo(url: str | None) -> tuple[str | None, str | None]:
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)/?$", (url or "").strip())
    return (match.group(1), match.group(2)) if match else (None, None)


def _owner_repo(item: ResearchItem) -> tuple[str | None, str | None]:
    owner = item.metadata.get("owner")
    repo = item.metadata.get("repo")
    if owner and repo:
        return owner, repo
    return _gh_url_owner_repo(item.canonical_url)


def item_identity(item: ResearchItem) -> str:
    """Stable source identity for an item — the migration merge key."""
    source = item.source
    if source == "github":
        if item.item_type == "search-result":
            return item.canonical_url or item.title
        owner, repo = _owner_repo(item)
        return f"{owner}/{repo}" if owner and repo else (item.canonical_url or item.title)
    if source == "papers":
        return arxiv_identity(item.canonical_url, item.title)
    if source == "wechat":
        return item.canonical_url or item.title
    if source == "hackernews":
        return str(item.metadata.get("item_id") or item.canonical_url or item.title)
    if source == "x":
        return str(item.metadata.get("post_id") or item.canonical_url or item.title)
    return item.canonical_url or item.title


def _relative_image_links(markdown_text: str) -> list[str]:
    return _IMAGE_RE.findall(markdown_text or "")


# --------------------------------------------------------------------------- #
# Target computation                                                          #
# --------------------------------------------------------------------------- #

def compute_target(item: ResearchItem) -> dict | None:
    """Return ``{kind, markdown, sidecar, dir}`` for an item's target (pure).

    ``None`` means the item has no relocatable primary material (e.g. a search
    batch, which is relocated as a whole by :func:`compute_batch_target`).
    """
    source = item.source
    if source == "github":
        if item.item_type == "search-result":
            return None
        owner, repo = _owner_repo(item)
        if not owner or not repo:
            return None
        paths = github_repo_paths(owner, repo)
        return {"kind": "move_dir", "markdown": paths["markdown"], "sidecar": paths["sidecar"], "dir": paths["dir"]}
    if source == "papers":
        ident = arxiv_identity(item.canonical_url, item.title)
        paths = paper_paths(ident)
        return {"kind": "move_file", "markdown": paths["markdown"], "sidecar": paths["sidecar"]}
    if source == "wechat":
        if item.item_type == "article-index":
            return None  # relocated as a whole ``_index`` batch by compute_batch_target
        paths = wechat_unit_paths(item.title, item.canonical_url, item.published_at, item.discovered_at)
        return {"kind": "move_dir_images", "markdown": paths["markdown"], "sidecar": paths["sidecar"], "dir": paths["dir"]}
    if source == "hackernews":
        paths = hackernews_paths(item.metadata.get("item_id"))
        return {"kind": "materialize", "markdown": paths["markdown"], "sidecar": paths["sidecar"]}
    if source == "x":
        paths = x_paths(item.metadata.get("post_id"))
        return {"kind": "materialize", "markdown": paths["markdown"], "sidecar": paths["sidecar"]}
    return None


def compute_batch_target(items: list[ResearchItem]) -> dict:
    """Relocate a shared-batch snapshot to its reserved namespace.

    - GitHub search: ``github/<query>/`` → ``github/_search/<query>-<ts>/``
    - WeChat public index: ``wechat/<account>/`` → ``wechat/_index/<account>-<ts>/``

    The snapshot keeps its current markdown filename (``search.md`` / ``signals.md``)
    so its internal references stay stable; only the containing directory changes.
    """
    source = items[0].source
    latest = None
    for item in items:
        if item.discovered_at and (latest is None or item.discovered_at > latest):
            latest = item.discovered_at
    md_name = PurePosixPath(items[0].output_path or "").name or "search.md"
    if source == "wechat":
        account = next((i.metadata.get("account") for i in items if i.metadata.get("account")), None)
        directory = f"wechat/{wechat_index_leaf(account, latest)}"
    else:
        query = next((i.metadata.get("query") for i in items if i.metadata.get("query")), None)
        if not query:
            query = PurePosixPath(items[0].output_path or "").parent.name.replace("-", " ")
        directory = github_search_dir(query, latest)
    return {"kind": "move_batch", "dir": directory,
            "markdown": f"{directory}/{md_name}", "sidecar": f"{directory}/research-items.jsonl",
            "md_name": md_name}


# --------------------------------------------------------------------------- #
# Load units                                                                  #
# --------------------------------------------------------------------------- #

@dataclass
class LegacyUnit:
    source: str
    sidecar: str
    markdown: str | None
    markdown_sha: str | None
    items: list[ResearchItem]
    batch: bool


def _collect_units(output_root: Path) -> list[LegacyUnit]:
    units: list[LegacyUnit] = []
    for sidecar_path in iter_research_item_sidecars(output_root):
        rel_sidecar = _rel(output_root, sidecar_path)
        top = PurePosixPath(rel_sidecar).parts[0] if PurePosixPath(rel_sidecar).parts else ""
        if top in PRESERVED_TOPDIRS:
            continue
        payloads = list(_iter_sidecar_payloads(sidecar_path))
        items = [item for item in (_item_from_payload(p) for p in payloads) if item is not None]
        if not items:
            continue
        is_batch = sidecar_path.name == "research-items.jsonl"
        markdown = None
        markdown_sha = None
        md_path = _resolve(output_root, items[0].output_path)
        if md_path is not None and md_path.is_file():
            markdown = _rel(output_root, md_path)
            markdown_sha = _sha256_file(md_path)
        units.append(LegacyUnit(source=items[0].source, sidecar=rel_sidecar, markdown=markdown,
                                markdown_sha=markdown_sha, items=items, batch=is_batch))
    return units


# --------------------------------------------------------------------------- #
# Plan model                                                                  #
# --------------------------------------------------------------------------- #

@dataclass
class MigrationPlan:
    output_root: str
    units: list[dict]                # every planned unit write
    merges: list[dict]               # merge groups (provenance recorded)
    collisions: list[dict]
    deletes: list[dict]              # superseded legacy paths to remove
    delete_orphans: list[dict]       # approved orphan deletions
    orphans: list[dict]              # unreferenced markdown needing manual review
    noop_count: int = 0

    def summary(self) -> dict:
        kinds: dict[str, int] = {}
        for unit in self.units:
            kinds[unit["kind"]] = kinds.get(unit["kind"], 0) + 1
        return {"units": len(self.units), "kinds": kinds, "merges": len(self.merges),
                "collisions": len(self.collisions), "deletes": len(self.deletes),
                "delete_orphans": len(self.delete_orphans), "orphans": len(self.orphans)}


def _is_empty_run_orphan(output_root: Path, rel_path: str) -> bool:
    path = _resolve(output_root, rel_path)
    if path is None or not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False
    return bool(re.search(r"Found 0 repositories", text))


def plan_migration(output_root: Path) -> MigrationPlan:
    """Compute the full migration plan without writing any file."""
    output_root = Path(output_root).resolve()
    units = _collect_units(output_root)
    plan = MigrationPlan(output_root=output_root.name, units=[], merges=[], collisions=[],
                         deletes=[], delete_orphans=[], orphans=[])

    # 1. Group every single-item unit by (source, identity) to detect merges.
    groups: dict[tuple[str, str], list[LegacyUnit]] = {}
    batch_units: list[LegacyUnit] = []
    for unit in units:
        if unit.batch and unit.source in ("hackernews", "x"):
            # A feed/query jsonl is exploded into per-item units by stable id.
            for item in unit.items:
                groups.setdefault((unit.source, item_identity(item)), []).append(
                    LegacyUnit(unit.source, unit.sidecar, unit.markdown, unit.markdown_sha, [item], False))
            batch_units.append(unit)
            continue
        if unit.batch:
            # github search / wechat public-index snapshots relocate whole.
            batch_units.append(unit)
            continue
        groups.setdefault((unit.source, item_identity(unit.items[0])), []).append(unit)

    for (source, identity), members in groups.items():
        _plan_group(output_root, plan, source, identity, members)

    for batch in batch_units:
        if batch.source in ("hackernews", "x"):
            continue  # exploded into per-item units via ``groups``
        _plan_batch(output_root, plan, batch)

    _plan_orphans(output_root, plan, units)
    plan.noop_count = sum(1 for u in plan.units if u["kind"] == "noop")
    return plan


def _plan_group(output_root: Path, plan: MigrationPlan, source: str, identity: str,
                members: list[LegacyUnit]) -> None:
    first = members[0].items[0]
    target = compute_target(first)
    if target is None:
        if first.output_path:
            plan.orphans.append({"path": first.output_path, "reason": "no-target-identity"})
        return

    if len(members) == 1:
        unit = members[0]
        already = unit.markdown == target["markdown"] and unit.sidecar == target["sidecar"]
        plan.units.append({
            "source": source, "identity": identity,
            "kind": "noop" if already else target["kind"],
            "target_markdown": target["markdown"], "target_sidecar": target["sidecar"],
            "target_dir": target.get("dir"),
            "from_markdown": unit.markdown, "from_sidecar": unit.sidecar,
            "from_dir": _current_unit_dir(output_root, unit),
            "items": [it.to_dict() for it in unit.items],
        })
        if not already and unit.markdown and unit.markdown != target["markdown"]:
            plan.deletes.append({"path": unit.markdown, "reason": "superseded by target"})
        if not already and unit.sidecar != target["sidecar"]:
            plan.deletes.append({"path": unit.sidecar, "reason": "superseded by target"})
        return

    # Multiple copies → merge only when equivalence proven.
    urls = {(item.canonical_url or item.title) for unit in members for item in unit.items}
    shas = {unit.markdown_sha for unit in members}
    # Content-bearing sources (github repo / papers / wechat) keep their own
    # markdown bytes, so a merge requires identical content *and* identity.
    # Materialized sources (hackernews / x) re-render the body from the item, so
    # the stable identity is the only equivalence proof available.
    if source in ("hackernews", "x"):
        equivalent = len(urls) <= 1
    else:
        equivalent = len(urls) <= 1 and len(shas) <= 1 and None not in shas
    copies = [{"markdown": unit.markdown, "sidecar": unit.sidecar, "markdown_sha": unit.markdown_sha,
               "feed": (unit.items[0].metadata.get("feed") if unit.items else None),
               "output_path": (unit.items[0].output_path if unit.items else None)} for unit in members]
    record = {"source": source, "identity": identity, "target_markdown": target["markdown"],
              "target_sidecar": target["sidecar"], "target_dir": target.get("dir"),
              "equivalent": equivalent, "copies": copies,
              "content_hashes": sorted({str(unit.markdown_sha) for unit in members}),
              "canonical_urls": sorted(str(u) for u in urls)}
    if not equivalent:
        record["reason"] = "conflicting content or identity; left in place for manual review"
        plan.collisions.append(record)
        return
    record["provenance"] = _merged_provenance(source, members)
    plan.merges.append(record)
    # Carry the survivor's own item so ``_merged_payload`` never has to parse a
    # JSONL batch file as if it were a single-object sidecar.
    survivor_unit = min(members, key=lambda u: u.sidecar)
    plan.units.append({
        "source": source, "identity": identity,
        "kind": target["kind"] if source not in ("hackernews", "x") else "materialize",
        "target_markdown": target["markdown"], "target_sidecar": target["sidecar"],
        "target_dir": target.get("dir"),
        "from_markdown": survivor_unit.markdown, "from_sidecar": survivor_unit.sidecar,
        "from_dir": _current_unit_dir(output_root, survivor_unit),
        "merge": True, "merge_record": record, "survivor_item": survivor_unit.items[0].to_dict(),
    })
    for unit in members:
        if unit.markdown:
            plan.deletes.append({"path": unit.markdown, "reason": "merged copy superseded"})
        plan.deletes.append({"path": unit.sidecar, "reason": "merged copy superseded"})


def _merged_provenance(source: str, members: list[LegacyUnit]) -> dict:
    provenance: dict = {}
    if source == "papers":
        categories: list[str] = []
        for unit in members:
            for item in unit.items:
                for tag in item.tags:
                    if tag not in categories:
                        categories.append(tag)
        provenance["categories"] = sorted(categories)
    if source in ("hackernews", "x"):
        feeds: list[str] = []
        ranks: list[dict] = []
        discovered: list[str] = []
        for unit in members:
            for item in unit.items:
                feed = item.metadata.get("feed") or item.metadata.get("query")
                if feed and feed not in feeds:
                    feeds.append(feed)
                if item.metadata.get("rank") is not None:
                    ranks.append({"feed": feed, "rank": item.metadata["rank"]})
                if item.discovered_at:
                    discovered.append(item.discovered_at)
        if feeds:
            provenance["feeds"] = feeds
        if ranks:
            provenance["ranks"] = ranks
        if discovered:
            provenance["discovered_dates"] = sorted(set(discovered))
    provenance["merged_from"] = sorted({unit.sidecar for unit in members})
    return provenance


def _plan_batch(output_root: Path, plan: MigrationPlan, batch: LegacyUnit) -> None:
    target = compute_batch_target(batch.items)
    already = batch.markdown == target["markdown"] and batch.sidecar == target["sidecar"]
    rewritten = []
    stored_md = _stored_output_path(output_root, target["markdown"])
    for item in batch.items:
        payload = item.to_dict()
        payload["output_path"] = stored_md
        rewritten.append(payload)
    plan.units.append({
        "source": batch.source, "identity": f"{batch.source}-batch:{target['dir']}",
        "kind": "noop" if already else "move_batch",
        "target_markdown": target["markdown"], "target_sidecar": target["sidecar"], "target_dir": target["dir"],
        "from_markdown": batch.markdown, "from_sidecar": batch.sidecar,
        "from_dir": _current_unit_dir(output_root, batch),
        "batch_items": rewritten, "batch_md_name": target.get("md_name", "search.md"),
    })
    if not already:
        if batch.markdown:
            plan.deletes.append({"path": batch.markdown, "reason": "snapshot batch relocated"})
        plan.deletes.append({"path": batch.sidecar, "reason": "snapshot batch relocated"})
        legacy_dir = PurePosixPath(batch.sidecar).parent.as_posix()
        plan.deletes.append({"path": legacy_dir + "/", "reason": "empty legacy snapshot dir", "dir": True})


def _current_unit_dir(output_root: Path, unit: LegacyUnit) -> str | None:
    if not unit.sidecar:
        return None
    return PurePosixPath(unit.sidecar).parent.as_posix()


def _plan_orphans(output_root: Path, plan: MigrationPlan, units: list[LegacyUnit]) -> None:
    referenced: set[str] = set()
    for unit in units:
        for item in unit.items:
            md = _resolve(output_root, item.output_path)
            if md is not None:
                referenced.add(_rel(output_root, md))
    for path in sorted(output_root.rglob("*.md")):
        rel = _rel(output_root, path)
        parts = PurePosixPath(rel).parts
        if not parts or parts[0] not in set(SOURCE_DIRS):
            continue
        if rel in referenced:
            continue
        if _is_empty_run_orphan(output_root, rel):
            plan.delete_orphans.append({"path": rel, "reason": "empty GitHub search run artifact"})
        else:
            plan.orphans.append({"path": rel, "reason": "unreferenced markdown"})


# --------------------------------------------------------------------------- #
# Manifest                                                                    #
# --------------------------------------------------------------------------- #

def build_migration_manifest(output_root: Path) -> dict:
    """Machine-readable pre-migration manifest of the whole archive."""
    output_root = Path(output_root).resolve()
    git_status = _load_git_status(output_root)
    files = []
    for path in sorted(output_root.rglob("*")):
        if not path.is_file():
            continue
        rel = _rel(output_root, path)
        posix_full = (Path(output_root.name) / rel).as_posix()
        files.append({
            "path": rel,
            "size": path.stat().st_size,
            "sha256": _sha256_file(path),
            "git_status": git_status.get(posix_full, git_status.get((output_root / rel).as_posix(), "untracked")),
        })

    units = _collect_units(output_root)
    sidecars = []
    for unit in units:
        md_text = ""
        if unit.markdown:
            md_path = _resolve(output_root, unit.markdown)
            if md_path is not None and md_path.is_file():
                try:
                    md_text = md_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    md_text = ""
        target = compute_target(unit.items[0]) if not unit.batch else compute_batch_target(unit.items)
        stored_target = _stored_output_path(output_root, (target or {}).get("markdown"))
        for item in unit.items:
            sidecars.append({
                "sidecar": unit.sidecar,
                "source": item.source,
                "identity": item_identity(item),
                "canonical_url": item.canonical_url,
                "output_path": item.output_path,
                "target_markdown": stored_target,
                "relative_image_links": _relative_image_links(md_text),
                "markdown_sha256": unit.markdown_sha,
                "batch": unit.batch,
            })
    return {
        "schema": "ai-intel-station/archive-migration-manifest/v1",
        "generated_at": utc_now_iso(),
        "output_root": str(output_root),
        "file_count": len(files),
        "item_count": len(sidecars),
        "files": files,
        "sidecars": sidecars,
        "plan": plan_migration(output_root).summary(),
    }


# --------------------------------------------------------------------------- #
# Backup / rollback boundary                                                  #
# --------------------------------------------------------------------------- #

@dataclass
class BackupResult:
    backup_dir: Path
    manifest_path: Path
    file_count: int
    combined_sha256: str


def _combined_tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        digest.update(_rel(root, path).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _overlaps(a: Path, b: Path) -> bool:
    """True when ``a`` equals ``b`` or either is an ancestor of the other."""
    return _is_within_or_equal(a, b) or _is_within_or_equal(b, a)


def _is_within_or_equal(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _assert_backup_topology_safe(output_root: Path, backup_dir: Path) -> None:
    """Reject any backup/restore layout that could delete the live archive.

    ``create_backup`` ``rmtree``s ``backup_dir / output_root.name`` before
    copying into it, and ``rollback`` ``rmtree``s ``output_root`` before
    restoring. Either delete is destructive exactly when the backup/restore tree
    coincides with or crosses the live archive, or the backup directory itself
    sits inside the archive. Safe sibling/ancestor directories that do not touch
    the archive are allowed.
    """
    output_root = Path(output_root).resolve()
    backup_dir = Path(backup_dir).resolve()
    backup_tree = backup_dir / output_root.name
    if _is_within_or_equal(backup_dir, output_root) or _overlaps(output_root, backup_tree):
        raise ValueError(
            "refusing unsafe backup topology: "
            f"output_root={output_root} vs backup_dir={backup_dir} "
            f"(backup tree {backup_tree}); proceeding could delete the archive"
        )


def create_backup(output_root: Path, backup_dir: Path) -> BackupResult:
    """Copy the whole archive + write its manifest into ``backup_dir`` (content-complete)."""
    output_root = Path(output_root).resolve()
    backup_dir = Path(backup_dir).resolve()
    _assert_backup_topology_safe(output_root, backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    target_output = backup_dir / output_root.name
    if target_output.exists():
        shutil.rmtree(target_output)
    shutil.copytree(output_root, target_output, symlinks=True)
    manifest = build_migration_manifest(target_output)
    manifest_path = backup_dir / "manifest.json"
    _atomic_write_text(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False))
    combined = _combined_tree_hash(target_output)
    (backup_dir / "BACKUP.json").write_text(json.dumps(
        {"schema": "v1", "created_at": utc_now_iso(), "source_output_root": str(output_root),
         "combined_sha256": combined}, indent=2), encoding="utf-8")
    file_count = sum(1 for p in target_output.rglob("*") if p.is_file())
    return BackupResult(backup_dir=backup_dir, manifest_path=manifest_path,
                        file_count=file_count, combined_sha256=combined)


def verify_backup(output_root: Path, backup: BackupResult) -> bool:
    """Self-check: the backup copy is content-complete against its manifest.

    This proves a *restore* would reproduce every recorded file hash. It does not
    require the live archive to still match — use :func:`backup_matches_tree` for
    the pre-migration boundary check.
    """
    restored_root = backup.backup_dir / Path(output_root).name
    if not restored_root.is_dir():
        return False
    try:
        manifest = json.loads(backup.manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    for entry in manifest["files"]:
        src = restored_root / entry["path"]
        if not src.is_file() or _sha256_file(src) != entry["sha256"]:
            return False
    return _combined_tree_hash(restored_root) == backup.combined_sha256


def backup_matches_tree(output_root: Path, backup: BackupResult) -> bool:
    """Prove the *live* archive still matches the backup manifest (no drift).

    The rollback boundary is only meaningful if it describes the current tree; if
    anything was added, removed or changed after the backup, this returns False
    and a migration must not start.
    """
    output_root = Path(output_root).resolve()
    try:
        manifest = json.loads(backup.manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    expected = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    live = {
        _rel(output_root, path): _sha256_file(path)
        for path in output_root.rglob("*") if path.is_file()
    }
    return live == expected


def rollback(output_root: Path, backup: BackupResult) -> None:
    """Restore the archive from a previously created backup (byte-for-byte)."""
    output_root = Path(output_root).resolve()
    _assert_backup_topology_safe(output_root, backup.backup_dir)
    restored_root = backup.backup_dir / output_root.name
    if not restored_root.is_dir():
        raise FileNotFoundError(f"backup tree missing under {restored_root}")
    if not verify_backup(output_root, backup):
        raise RuntimeError("refusing to roll back: backup manifest does not verify")
    if output_root.exists():
        shutil.rmtree(output_root)
    shutil.copytree(restored_root, output_root, symlinks=True)


# --------------------------------------------------------------------------- #
# Apply                                                                       #
# --------------------------------------------------------------------------- #

@dataclass
class MigrationResult:
    relocated: int = 0
    merged: int = 0
    materialized: int = 0
    batches: int = 0
    deleted_orphans: int = 0
    collisions: int = 0
    noop: int = 0
    errors: list[str] = field(default_factory=list)


def apply_migration(output_root: Path, *, require_verified_backup: Path,
                    plan: MigrationPlan | None = None) -> MigrationResult:
    """Execute an atomic, idempotent migration of ``output_root``.

    ``require_verified_backup`` is mandatory: it must point at a backup whose
    manifest still matches the current tree. There is no public path that bulk
    moves or deletes archive material without a verified rollback boundary; the
    raw mutation lives in the private :func:`_execute_migration`.
    """
    output_root = Path(output_root).resolve()
    if require_verified_backup is None:
        raise RuntimeError("migration aborted: a verified backup boundary is required")
    probe = BackupResult(backup_dir=Path(require_verified_backup),
                         manifest_path=Path(require_verified_backup) / "manifest.json",
                         file_count=0, combined_sha256="")
    try:
        probe.combined_sha256 = json.loads((Path(require_verified_backup) / "BACKUP.json")
                                           .read_text(encoding="utf-8"))["combined_sha256"]
    except (OSError, json.JSONDecodeError, KeyError):
        raise RuntimeError("migration aborted: rollback boundary is missing its BACKUP.json")
    if not verify_backup(output_root, probe) or not backup_matches_tree(output_root, probe):
        raise RuntimeError("migration aborted: verified backup/rollback boundary is stale")
    return _execute_migration(output_root, plan)


def _execute_migration(output_root: Path, plan: MigrationPlan | None = None) -> MigrationResult:
    """Private raw mutation. Callers must already hold a verified backup boundary."""
    output_root = Path(output_root).resolve()
    plan = plan or plan_migration(output_root)
    result = MigrationResult()

    written_targets: set[str] = set()
    for unit in plan.units:
        try:
            _apply_unit(output_root, unit, result, written_targets)
        except Exception as exc:  # each file write is atomic; keep prior progress
            result.errors.append(f"unit {unit.get('target_sidecar')}: {exc}")

    for orphan in plan.delete_orphans:
        try:
            _apply_delete(output_root, orphan["path"], result)
            result.deleted_orphans += 1
        except Exception as exc:
            result.errors.append(f"delete-orphan {orphan.get('path')}: {exc}")

    _remove_superseded(output_root, plan.deletes, written_targets, result)
    _cleanup_empty_dirs(output_root)
    result.collisions = len(plan.collisions)
    result.noop = plan.noop_count
    return result


def _write_target_markdown(output_root: Path, unit: dict, item: ResearchItem) -> None:
    md_rel = unit["target_markdown"]
    md = _resolve(output_root, md_rel)
    if md is None:
        return
    if md.is_file():
        return
    if item.source == "hackernews":
        _atomic_write_text(md, render_hackernews_markdown(item))
    elif item.source == "x":
        _atomic_write_text(md, render_x_markdown(item))
    else:  # move/copy of an existing markdown body
        src = _resolve(output_root, unit.get("from_markdown"))
        if src is not None and src.is_file():
            md.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, md)


def _apply_unit(output_root: Path, unit: dict, result: MigrationResult, written: set[str]) -> None:
    kind = unit["kind"]
    if kind == "noop":
        return
    target_sidecar = unit["target_sidecar"]

    if kind == "move_batch":
        _apply_batch(output_root, unit, result)
        written.update({unit["target_markdown"], unit["target_sidecar"]})
        return

    # Build the (possibly merged) sidecar payload.
    was_merge = bool(unit.get("merge"))
    if unit.get("merge"):
        payload = _merged_payload(output_root, unit)
    else:
        payload = unit["items"][0] if unit.get("items") else _read_payload(output_root / unit["from_sidecar"])
        payload = dict(payload) if payload else {}
        payload["output_path"] = _stored_output_path(output_root, unit["target_markdown"])

    if kind == "move_dir_images":
        _move_wechat_unit(output_root, unit, payload, result, written)
        if was_merge:
            result.merged += 1
        return

    if kind == "move_dir":
        _move_github_repo(output_root, unit, payload, result, written)
        if was_merge:
            result.merged += 1
        return

    # move_file (papers) and materialize (hn/x): write markdown then sidecar.
    item = _item_from_payload(payload)
    if item is not None:
        _write_target_markdown(output_root, {**unit, "from_markdown": unit.get("from_markdown")}, item)
    _atomic_write_text(output_root / target_sidecar, json.dumps(payload, ensure_ascii=False))
    written.update({p for p in (unit.get("target_markdown"), target_sidecar) if p})
    if kind == "materialize":
        result.materialized += 1
    else:
        result.relocated += 1
    if was_merge:
        result.merged += 1


def _move_wechat_unit(output_root: Path, unit: dict, payload: dict, result: MigrationResult, written: set[str]) -> None:
    from_dir = output_root / unit["from_dir"]
    to_dir = output_root / unit["target_dir"]
    if from_dir.exists() and from_dir.resolve() != to_dir.resolve():
        to_dir.parent.mkdir(parents=True, exist_ok=True)
        if to_dir.exists():
            _merge_dir_into(to_dir, from_dir)
        else:
            os.replace(from_dir, to_dir)
    # Rename inner markdown to the target basename and rewrite its sidecar.
    _normalize_unit_markdown(to_dir, Path(unit["target_markdown"]).name)
    _atomic_write_text(to_dir / "research-item.json", json.dumps(payload, ensure_ascii=False))
    written.update({unit["target_markdown"], unit["target_sidecar"]})
    # Images ride inside the dir; relative links keep resolving.
    for md in to_dir.glob("*.md"):
        text = md.read_text(encoding="utf-8")
        for link in _relative_image_links(text):
            if not (md.parent / link).is_file():
                result.errors.append(f"broken image link {link} in {md}")
    result.relocated += 1


def _move_github_repo(output_root: Path, unit: dict, payload: dict, result: MigrationResult, written: set[str]) -> None:
    from_dir = output_root / unit["from_dir"]
    to_dir = output_root / unit["target_dir"]
    if from_dir.exists() and from_dir.resolve() != to_dir.resolve():
        to_dir.parent.mkdir(parents=True, exist_ok=True)
        if to_dir.exists():
            _merge_dir_into(to_dir, from_dir)
        else:
            os.replace(from_dir, to_dir)
    _normalize_unit_markdown(to_dir, Path(unit["target_markdown"]).name)
    _atomic_write_text(to_dir / "research-item.json", json.dumps(payload, ensure_ascii=False))
    written.update({unit["target_markdown"], unit["target_sidecar"]})
    result.relocated += 1


def _merge_dir_into(target_dir: Path, source_dir: Path) -> None:
    for item in source_dir.rglob("*"):
        if item.is_file():
            rel = item.relative_to(source_dir)
            dst = target_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                os.replace(item, dst)


def _normalize_unit_markdown(unit_dir: Path, target_name: str) -> None:
    """Ensure the single article markdown inside ``unit_dir`` is named ``target_name``."""
    desired = unit_dir / target_name
    if desired.is_file():
        return
    candidates = [p for p in sorted(unit_dir.glob("*.md")) if p.name != target_name]
    if candidates:
        os.replace(candidates[0], desired)


def _apply_batch(output_root: Path, unit: dict, result: MigrationResult) -> None:
    to_dir = output_root / unit["target_dir"]
    from_dir = output_root / unit["from_dir"]
    to_dir.parent.mkdir(parents=True, exist_ok=True)
    md_name = unit.get("batch_md_name", "search.md")
    if from_dir.exists() and from_dir.resolve() != to_dir.resolve():
        md_src = _resolve(output_root, unit["from_markdown"])
        md_dst = to_dir / md_name
        if md_src is not None and md_src.is_file():
            md_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(md_src, md_dst)
    lines = [json.dumps(payload, ensure_ascii=False) for payload in unit.get("batch_items", [])]
    _atomic_write_text(to_dir / "research-items.jsonl", ("\n".join(lines) + "\n") if lines else "")
    result.batches += 1


def _read_payload(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _merged_payload(output_root: Path, unit: dict) -> dict:
    """Union provenance across proven-equivalent copies, anchored on the survivor."""
    merge = unit.get("merge_record") or {}
    copies = merge.get("copies") or [{"sidecar": unit["from_sidecar"]}]
    # Prefer the survivor item carried by the plan; only fall back to reading a
    # single-object sidecar (never a JSONL batch) for merged non-batch sources.
    if unit.get("survivor_item"):
        survivor = dict(unit["survivor_item"])
    else:
        survivor_rel = min(c["sidecar"] for c in copies)
        survivor = _read_payload(output_root / survivor_rel) or {}
    survivor["output_path"] = _stored_output_path(output_root, unit["target_markdown"])
    provenance = merge.get("provenance", {})
    metadata = dict(survivor.get("metadata") or {})
    if provenance.get("categories"):
        metadata["categories"] = provenance["categories"]
        survivor["tags"] = sorted(set(survivor.get("tags") or []) | set(provenance["categories"]))
    for key in ("feeds", "ranks", "discovered_dates"):
        if provenance.get(key):
            metadata[key] = provenance[key]
    if unit["source"] in ("hackernews", "x") and len(copies) > 1:
        metadata.setdefault("feeds", sorted({c.get("feed") for c in copies if c.get("feed")}))
    migrated = sorted({c["markdown"] for c in copies if c.get("markdown")})
    if migrated:
        metadata["migrated_from"] = migrated
    survivor["metadata"] = {k: v for k, v in metadata.items() if v not in (None, "", [], {})}
    return survivor


def _apply_delete(output_root: Path, rel_path: str, result: MigrationResult) -> None:
    path = _resolve(output_root, rel_path)
    if path is not None and path.is_file():
        path.unlink()


def _remove_superseded(output_root: Path, deletes: list[dict], written: set[str], result: MigrationResult) -> None:
    seen: set[str] = set()
    for entry in deletes:
        rel = entry["path"]
        if rel in seen:
            continue
        seen.add(rel)
        if rel.rstrip("/") in {p.rstrip("/") for p in written}:
            continue
        if entry.get("dir"):
            path = _resolve(output_root, rel.rstrip("/"))
            if path is not None and path.is_dir() and not any(path.iterdir()):
                try:
                    path.rmdir()
                except OSError:
                    pass
            continue
        # Only delete a markdown/sidecar that is NOT itself a written target and
        # whose content has been reproduced elsewhere.
        if rel in written:
            continue
        path = _resolve(output_root, rel)
        if path is not None and path.is_file():
            path.unlink()


def _cleanup_empty_dirs(output_root: Path) -> None:
    for path in sorted((p for p in output_root.rglob("*") if p.is_dir()), key=lambda p: -len(p.parts)):
        parts = PurePosixPath(_rel(output_root, path)).parts
        if not parts or parts[0] not in set(SOURCE_DIRS) or parts[0] in PRESERVED_TOPDIRS:
            continue
        try:
            if not any(path.iterdir()):
                path.rmdir()
        except OSError:
            continue


# --------------------------------------------------------------------------- #
# Rendering (single rule shared with the collectors — see library.items)       #
# --------------------------------------------------------------------------- #

render_hackernews_markdown = hackernews_story_markdown
render_x_markdown = x_post_markdown


# --------------------------------------------------------------------------- #
# Verification                                                                #
# --------------------------------------------------------------------------- #

def verify_migration(output_root: Path) -> dict:
    """Prove every ResearchItem.output_path resolves and report remaining dup ids."""
    from ai_intel_station.library.storage import load_research_items

    output_root = Path(output_root).resolve()
    items = load_research_items(output_root)
    missing_targets = []
    broken_images = []
    for item in items:
        if not item.output_path:
            continue
        md = _resolve(output_root, item.output_path)
        if md is None or not md.is_file():
            missing_targets.append({"source": item.source, "identity": item_identity(item),
                                    "output_path": item.output_path})
            continue
        try:
            text = md.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for link in _relative_image_links(text):
            if not (md.parent / link).is_file():
                broken_images.append({"markdown": _rel(output_root, md), "image": link})
    identities: dict[str, int] = {}
    for item in items:
        key = f"{item.source}::{item_identity(item)}"
        identities[key] = identities.get(key, 0) + 1
    remaining_dups = {k: v for k, v in identities.items() if v > 1}
    return {"item_count": len(items), "missing_targets": missing_targets,
            "broken_images": broken_images, "remaining_duplicate_identities": remaining_dups}
