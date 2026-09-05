import asyncio
from pathlib import Path

from briefing.service import build_generic_briefing, save_generic_briefing
from collect.papers import CATEGORIES_HELP
from collect.service import collect_github, collect_papers, collect_wechat
from collect.wechat import (
    WeChatRuntimeDependencyError,
)
from library.service import (
    backfill_library,
    display_archive_path,
    organize_library,
    search_library,
)
from research.discovery import (
    DEFAULT_CONFIG_PATH,
    EXAMPLE_CONFIG_PATH,
    DiscoveryConfigError,
    load_config,
    render_example_config,
    run_discovery,
)
from workspace_web.server import serve_workspace


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"
SCRIPTS_DIR = REPO_ROOT / "scripts"


def collect_github_targets(targets: list[str], output_root: Path, search: bool = False) -> None:
    result = collect_github(targets, output_root, search=search)
    for failure in result.failures:
        print(f"⚠️  {failure}")
    if result.status == "error":
        raise ValueError(result.message)


def collect_paper_categories(categories: list[str], output_root: Path, max_results: int = 10) -> None:
    if not categories:
        print("⚠️  Please specify at least one category. Use --list to see available categories.")
        print(CATEGORIES_HELP)
        return

    result = collect_papers(categories, output_root, max_results=max_results)
    if result.status == "error":
        raise ValueError(result.message)


async def collect_wechat_article(url: str, output_root: Path) -> None:
    result = await collect_wechat(url, output_root)
    if result.status == "error":
        raise ValueError(result.message)


def render_query_results(output_root: Path, keyword: str, sources: list[str] | None, since: str | None, until: str | None) -> str:
    items = search_library(output_root, keyword=keyword, sources=sources, since=since, until=until)
    if not items:
        return "No matching research items found."

    lines = []
    for item in items:
        lines.append(f"- [{item.source}] {item.title}")
        if item.canonical_url:
            lines.append(f"  {item.canonical_url}")
    return "\n".join(lines)


def list_briefings(output_root: Path) -> int:
    briefing_root = Path(output_root) / "briefing"
    if not briefing_root.exists():
        print(f"📭 No briefing directory under {briefing_root}.")
        print("   Run a discovery sweep first:  uv run research discover")
        return 0

    found: list[Path] = []
    for section in ("signals", "digests", "reading-lists"):
        section_dir = briefing_root / section
        if section_dir.exists():
            found.extend(sorted(section_dir.glob("*.md"), reverse=True))
    if not found:
        print(f"📭 No briefing markdown found under {briefing_root}.")
        return 0

    output_root = Path(output_root).resolve()
    print(f"📰 {len(found)} briefing file(s) under {briefing_root}:")
    for path in found:
        print(f"  • {display_archive_path(path, output_root)}")
    return 0


def generate_briefing(
    mode: str,
    keyword: str,
    output_root: Path,
    title: str | None = None,
    sources: list[str] | None = None,
    since: str | None = None,
    until: str | None = None,
) -> Path:
    briefing = build_generic_briefing(
        output_root,
        mode=mode,
        keyword=keyword,
        title=title,
        sources=sources,
        since=since,
        until=until,
    )
    saved = save_generic_briefing(briefing, output_root)
    assert saved.path is not None
    return saved.path


def run_backfill(output_root: Path) -> list[Path]:
    return backfill_library(output_root)


def run_organize(output_root: Path) -> int:
    catalog = organize_library(output_root)
    print(f"Organized {catalog.item_count} ResearchItem(s) without moving primary archive.")
    print(
        f"Sources: {len(catalog.source_counts)}; tags: {catalog.tag_count}; "
        f"untagged: {catalog.untagged_count}; undated: {catalog.undated_count}; "
        f"duplicate URL groups: {catalog.duplicate_groups}; "
        f"orphan Markdown: {catalog.orphan_markdown_count}"
    )
    for path in catalog.paths:
        print(f"  {display_archive_path(path, output_root)}")
    return 0


_MIGRATION_STATE_DIR = REPO_ROOT / ".state" / "migration"


def run_migrate(
    output_root: Path,
    *,
    apply: bool = False,
    manifest_path: Path | None = None,
    backup_dir: Path | None = None,
    rollback_from: Path | None = None,
) -> int:
    """Drive the shared archive migration service (``library.migration``).

    Default is a safe dry-run: it prints the plan without writing. ``--apply``
    first materializes a verified backup + manifest (the rollback boundary), then
    runs the atomic idempotent migration, rebuilds the Library catalog and proves
    missing targets / broken links / unresolved collisions are zero.
    """
    from library import migration

    output_root = Path(output_root)

    if rollback_from is not None:
        backup = migration.BackupResult(
            backup_dir=Path(rollback_from),
            manifest_path=Path(rollback_from) / "manifest.json",
            file_count=0,
            combined_sha256="",
        )
        try:
            import json as _json
            backup.combined_sha256 = _json.loads(
                (Path(rollback_from) / "BACKUP.json").read_text(encoding="utf-8")
            )["combined_sha256"]
        except (OSError, ValueError, KeyError):
            print(f"❌ {rollback_from} is not a valid rollback boundary (missing BACKUP.json).")
            return 2
        migration.rollback(output_root, backup)
        print(f"↩ Rolled back {output_root} from {rollback_from}.")
        return 0

    plan = migration.plan_migration(output_root)
    summary = plan.summary()
    print(f"Migration plan for {output_root}:")
    print(f"  units={summary['units']} kinds={summary['kinds']}")
    print(f"  merges={summary['merges']} collisions={summary['collisions']} "
          f"deletes={summary['deletes']} delete_orphans={summary['delete_orphans']} "
          f"orphans={summary['orphans']}")
    for collision in plan.collisions:
        print(f"  ⚠ collision {collision['source']}::{collision['identity']} -> {collision['target_markdown']}"
              f" ({collision.get('reason')})")
    for orphan in plan.orphans:
        print(f"  ⚠ orphan {orphan['path']} ({orphan['reason']})")
    for orphan in plan.delete_orphans:
        print(f"  · will delete empty-run artifact {orphan['path']}")

    if not apply:
        print("Dry run complete. Pass --apply to migrate (requires a verified backup).")
        return 0

    boundary = Path(backup_dir) if backup_dir else _MIGRATION_STATE_DIR / _utc_slug()
    backup = migration.create_backup(output_root, boundary)
    if not migration.verify_backup(output_root, backup) or not migration.backup_matches_tree(output_root, backup):
        print("❌ Refusing to migrate: rollback boundary did not verify.")
        return 2
    print(f"✅ Rollback boundary ready: {boundary} ({backup.file_count} files, sha {backup.combined_sha256[:12]})")
    if manifest_path is not None:
        import json as _json
        Path(manifest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(manifest_path).write_text(
            _json.dumps(migration.build_migration_manifest(output_root), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"🗒 Manifest written: {manifest_path}")

    result = migration.apply_migration(output_root, require_verified_backup=boundary)
    print(f"Migrated: relocated={result.relocated} merged={result.merged} materialized={result.materialized} "
          f"batches={result.batches} deleted_orphans={result.deleted_orphans} collisions={result.collisions} noop={result.noop}")
    for err in result.errors:
        print(f"  ❌ {err}")

    organize_library(output_root)
    report = migration.verify_migration(output_root)
    missing = report["missing_targets"]
    broken = report["broken_images"]
    remaining = report["remaining_duplicate_identities"]
    print(f"Verify: items={report['item_count']} missing_targets={len(missing)} "
          f"broken_images={len(broken)} remaining_duplicate_identities={len(remaining)}")
    for m in missing[:10]:
        print(f"  ❌ missing {m['source']}::{m['identity']} -> {m['output_path']}")
    for b in broken[:10]:
        print(f"  ❌ broken image {b['markdown']} -> {b['image']}")
    for k, v in list(remaining.items())[:10]:
        print(f"  ⚠ unresolved duplicate identity {k} x{v}")

    if result.errors or missing or broken or remaining or result.collisions:
        print("❌ Migration left unresolved items; archive NOT fully converged. Roll back with:")
        print(f"   uv run research migrate archive --rollback {boundary} -o {output_root}")
        return 1
    print("✅ Archive fully migrated; catalog rebuilt with zero missing/broken/collision.")
    return 0


def _utc_slug() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run_web_workspace(output_root: Path) -> None:
    serve_workspace(output_root)


def _resolve_discovery_log_dir(config_path: Path) -> Path:
    log_dir = None
    if config_path.exists():
        try:
            config = load_config(config_path)
            log_dir = config.log_dir
        except DiscoveryConfigError as exc:
            print(f"⚠️  Could not load config ({exc}); falling back to default log dir.")
    if log_dir is None:
        from research.discovery.config import DEFAULT_LOG_DIR
        log_dir = DEFAULT_LOG_DIR
    return log_dir


def run_discover_status(config_path: Path, *, last: int = 1) -> int:
    from research.discovery import latest_log_path, read_log_summary, recent_log_paths

    log_dir = _resolve_discovery_log_dir(config_path)

    if last <= 1:
        path = latest_log_path(log_dir)
        if path is None:
            print(f"📭 No discovery log found under {log_dir}.")
            print("   Try:  uv run research discover --dry-run")
            return 0

        info = read_log_summary(path)
        print(f"📓 Latest log: {info['path']}")
        if info["started_at"]:
            print(f"   started_at:  {info['started_at']}")
        if info["finished_at"]:
            print(f"   finished_at: {info['finished_at']}")
        if info["summary"]:
            print(f"   {info['summary']}")
        if info["briefing"]:
            print(f"   📰 {info['briefing']}")
        if info.get("briefing_status"):
            print(f"   briefing_status: {info['briefing_status']}")
        return 0

    paths = recent_log_paths(log_dir, limit=last)
    if not paths:
        print(f"📭 No discovery logs found under {log_dir}.")
        print("   Try:  uv run research discover --dry-run")
        return 0

    print(f"📓 Last {len(paths)} runs under {log_dir}:")
    for path in paths:
        info = read_log_summary(path)
        marker = info["summary"] or "(no summary)"
        when = info["started_at"] or "?"
        print(f"  • {path.name}  started={when}  {marker}")
    return 0


def run_discover(
    config_path: Path,
    *,
    only: list[str] | None,
    dry_run: bool,
    output_root: Path,
    enable_briefing: bool = True,
    status_only: bool = False,
    log_list: int = 0,
) -> int:
    if log_list > 0:
        return run_discover_status(config_path, last=log_list)
    if status_only:
        return run_discover_status(config_path, last=1)

    if config_path == DEFAULT_CONFIG_PATH and not config_path.exists():
        if dry_run:
            # In dry-run we can safely fall back to the example: the user just
            # wants to see what a sweep looks like, and no network calls happen.
            if EXAMPLE_CONFIG_PATH.exists():
                print(
                    f"⚠️  No config at {config_path}; using {EXAMPLE_CONFIG_PATH} for the dry-run preview."
                )
                config_path = EXAMPLE_CONFIG_PATH
            else:
                print(
                    f"❌ No config at {config_path} and no example template found. "
                    f"Run: uv run research init-config"
                )
                return 2
        else:
            print(
                f"❌ No config at {config_path}.\n"
                f"   Set one up first: uv run research init-config\n"
                f"   Or pass --dry-run to preview with the bundled example."
            )
            return 2

    try:
        config = load_config(config_path)
    except DiscoveryConfigError as exc:
        print(f"❌ {exc}")
        return 2

    if output_root != DEFAULT_OUTPUT_ROOT:
        config.output_root = output_root

    report = run_discovery(
        config,
        only=only,
        dry_run=dry_run,
        enable_briefing=enable_briefing,
    )
    print(f"📓 Log: {report.log_path}")
    briefing_failed = bool(report.briefing and report.briefing.status == "failed")
    return 0 if not any(r.failed for r in report.sources.values()) and not briefing_failed else 1


VALID_SOURCES = ("github", "papers", "wechat", "hackernews", "x")


def _parse_source_list(values: list[str] | None) -> list[str] | None:
    """Accept either repeated --source or --source a,b forms.

    Returns ``None`` when no values were given. Raises ``ArgumentTypeError`` on
    any unknown source so argparse prints a clean error.
    """
    if not values:
        return None
    expanded: list[str] = []
    for raw in values:
        for piece in raw.split(","):
            piece = piece.strip()
            if not piece:
                continue
            if piece not in VALID_SOURCES:
                import argparse as _argparse

                raise _argparse.ArgumentTypeError(
                    f"invalid source {piece!r}; choose from {', '.join(VALID_SOURCES)}"
                )
            if piece not in expanded:
                expanded.append(piece)
    return expanded or None


def run_init_config(target: Path, *, force: bool = False) -> int:
    """Write the bundled example discovery config to ``target`` and print
    next-step guidance so first-time users know exactly what to run next."""
    if target.exists() and not force:
        print(f"❌ {target} already exists. Pass --force to overwrite.")
        return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_example_config(), encoding="utf-8")
    print(f"✅ Wrote example config to {target}")
    print()
    print("Next steps:")
    print(f"  1. Edit {target}  (set your GitHub repos / arXiv categories / etc.)")
    print(f"  2. uv run research discover --dry-run --config {target}")
    print("     ↳ See what would be collected, with NO network calls.")
    print(f"  3. uv run research discover --config {target}  # actually run")
    print()
    print("When you're happy with the output, install the daily schedule:")
    print("  uv run research schedule launchd --install   # macOS, one-shot")
    print("  uv run research schedule cron                # Linux / fallback")
    return 0


def run_schedule(platform: str, install: bool = False) -> int:
    from research.discovery.scripts import (
        install_cron,
        install_launchd,
        render_install_instructions,
    )

    if not install:
        print(render_install_instructions(platform, REPO_ROOT))
        return 0

    if platform == "launchd":
        path, output = install_launchd(REPO_ROOT)
        print(f"✅ Installed plist: {path}")
        print(f"   launchctl output: {output or '(none)'}")
        print("   Verify:  launchctl list | grep com.ai-intel-station.daily")
        print("   Unload:  launchctl unload ~/Library/LaunchAgents/com.ai-intel-station.daily.plist")
        return 0

    if platform == "cron":
        output, backup = install_cron(REPO_ROOT)
        print(f"✅ Installed crontab. Backup at {backup}")
        print(f"   launchctl/cron output: {output or '(none)'}")
        print("   Verify:  crontab -l | grep ai-intel-station")
        return 0

    print(f"❌ Unknown platform: {platform}")
    return 2
