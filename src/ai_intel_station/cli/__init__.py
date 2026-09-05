from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from ai_intel_station.collect.papers import CATEGORIES_HELP
from ai_intel_station.collect.wechat import WeChatRuntimeDependencyError
from ai_intel_station.cli.commands import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_OUTPUT_ROOT,
    VALID_SOURCES,
    collect_github_targets,
    collect_paper_categories,
    collect_wechat_article,
    generate_briefing,
    list_briefings,
    render_query_results,
    run_backfill,
    run_discover,
    run_init_config,
    run_migrate,
    run_organize,
    run_schedule,
    run_web_workspace,
)

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified operator surface for AI Intel Station")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect", help="Collect raw material into the local archive")
    collect_subparsers = collect_parser.add_subparsers(dest="source", required=True)

    github_parser = collect_subparsers.add_parser("github", help="Collect GitHub repositories or search results")
    github_parser.add_argument("targets", nargs="+", help="owner/repo or a search query")
    github_parser.add_argument("--search", action="store_true", help="Treat targets as a GitHub search query")
    github_parser.add_argument("--issues", action="store_true", help="Accepted for parity with previous runtime behavior")
    github_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    papers_parser = collect_subparsers.add_parser("papers", help="Collect arXiv papers by category")
    papers_parser.add_argument("categories", nargs="*", help="arXiv categories, for example cs.AI")
    papers_parser.add_argument("--max", type=int, default=10, help="Max papers per category")
    papers_parser.add_argument("--list", action="store_true", help="List supported AI categories")
    papers_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    wechat_parser = collect_subparsers.add_parser("wechat", help="Collect one WeChat article")
    wechat_parser.add_argument("url", help="WeChat article URL")
    wechat_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    query_parser = subparsers.add_parser("query", help="Query local sidecars without remote fetches")
    query_parser.add_argument("keyword")
    query_parser.add_argument("--source", action="append", dest="sources")
    query_parser.add_argument("--since")
    query_parser.add_argument("--until")
    query_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    briefing_parser = subparsers.add_parser("briefing", help="Generate or list briefing artifacts from local sidecars")
    briefing_parser.add_argument("mode", nargs="?", choices=["digest", "reading-list"], help="Required unless --list is passed")
    briefing_parser.add_argument("keyword", nargs="?")
    briefing_parser.add_argument("--title")
    briefing_parser.add_argument("--source", action="append", dest="sources")
    briefing_parser.add_argument("--since")
    briefing_parser.add_argument("--until")
    briefing_parser.add_argument("--list", action="store_true", help="List existing briefing markdown files")
    briefing_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    backfill_parser = subparsers.add_parser("backfill", help="Backfill ResearchItem sidecars from historical Markdown")
    backfill_parser.add_argument("output_root", nargs="?", type=Path, default=DEFAULT_OUTPUT_ROOT)

    organize_parser = subparsers.add_parser(
        "organize",
        help="Build date/tag/duplicate catalogs without moving the primary archive",
    )
    organize_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Reorganize the physical archive to source + stable identity paths",
    )
    migrate_sub = migrate_parser.add_subparsers(dest="migrate_target", required=True)
    archive_parser = migrate_sub.add_parser(
        "archive", help="Plan (default) or apply the archive layout migration"
    )
    archive_parser.add_argument("--apply", action="store_true",
                                help="Actually move/merge files (default is a safe dry-run)")
    archive_parser.add_argument("--manifest", type=Path, default=None,
                                help="Write the machine-readable pre-migration manifest here")
    archive_parser.add_argument("--backup-dir", type=Path, default=None,
                                help="Where to create the rollback boundary backup")
    archive_parser.add_argument("--rollback", type=Path, default=None,
                                help="Restore the archive from a prior backup directory")
    archive_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    web_parser = subparsers.add_parser("web", help="Launch the local web workspace")
    web_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    discover_parser = subparsers.add_parser(
        "discover",
        help="Run the configured daily signal sweep and briefing",
        epilog=(
            "First time? Run these in order:\n"
            "  uv run research init-config\n"
            "  uv run research discover --dry-run\n"
            "  uv run research discover\n"
            "See doc/daily_discovery_design.md for the full guide."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    discover_parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Discovery YAML (default: {DEFAULT_CONFIG_PATH})",
    )
    discover_parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help=(
            "Limit the sweep to github|papers|wechat|hackernews|x "
            "(repeatable, or comma-separated)"
        ),
    )
    discover_parser.add_argument(
        "--no-briefing",
        action="store_true",
        help="Skip the briefing step even if config.briefing.enabled is true",
    )
    discover_parser.add_argument("--dry-run", action="store_true", help="Plan only; never touch the network")
    discover_parser.add_argument(
        "--status",
        action="store_true",
        help="Print the most recent run's summary (no network, no rerun)",
    )
    discover_parser.add_argument(
        "--log-list",
        type=int,
        default=0,
        metavar="N",
        help="Print summaries of the most recent N runs (no network, no rerun)",
    )
    discover_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    schedule_parser = subparsers.add_parser(
        "schedule", help="Print install instructions for daily launchd/cron scheduling"
    )
    schedule_parser.add_argument("platform", choices=["launchd", "cron"])
    schedule_parser.add_argument(
        "--install",
        action="store_true",
        help="Actually install (write plist + launchctl load / write crontab) instead of just printing",
    )

    init_parser = subparsers.add_parser(
        "init-config", help="Write the example discovery config to a target path"
    )
    init_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Where to write the example config (default: {DEFAULT_CONFIG_PATH})",
    )
    init_parser.add_argument("--force", action="store_true", help="Overwrite if it already exists")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse calls sys.exit on parse errors — bubble up unchanged.
        raise

    try:
        return _dispatch(args)
    except WeChatRuntimeDependencyError as exc:
        print(f"❌ {exc}")
        return 2
    except ValueError as exc:
        # User-input date filters or config errors raise ValueError from
        # query_research_items / load_config. Surface a one-line message
        # instead of a full traceback so the CLI stays operator-friendly.
        print(f"❌ {exc}")
        return 2


def _dispatch(args) -> int:

    if args.command == "collect":
        if args.source == "github":
            collect_github_targets(args.targets, args.output_root, search=args.search)
            return 0
        if args.source == "papers":
            if args.list:
                print(CATEGORIES_HELP)
                return 0
            collect_paper_categories(args.categories, args.output_root, max_results=args.max)
            return 0
        asyncio.run(collect_wechat_article(args.url, args.output_root))
        return 0

    if args.command == "query":
        print(render_query_results(args.output_root, args.keyword, args.sources, args.since, args.until))
        return 0

    if args.command == "briefing":
        if args.list:
            return list_briefings(args.output_root)
        if not args.mode or not args.keyword:
            print("❌ briefing requires <mode> <keyword>, or pass --list")
            return 2
        saved = generate_briefing(
            args.mode,
            args.keyword,
            args.output_root,
            title=args.title,
            sources=args.sources,
            since=args.since,
            until=args.until,
        )
        print(f"Saved briefing: {saved}")
        return 0

    if args.command == "web":
        run_web_workspace(args.output_root)
        return 0

    if args.command == "discover":
        # Accept both --source a --source b and --source a,b; dedupe while preserving order.
        only: list[str] = []
        for raw in args.sources or []:
            for piece in raw.split(","):
                piece = piece.strip()
                if piece and piece in VALID_SOURCES and piece not in only:
                    only.append(piece)
                elif piece and piece not in VALID_SOURCES:
                    print(
                        f"❌ invalid source {piece!r}; choose from {', '.join(VALID_SOURCES)}"
                    )
                    return 2
        return run_discover(
            args.config,
            only=only or None,
            dry_run=args.dry_run,
            output_root=args.output_root,
            enable_briefing=not args.no_briefing,
            status_only=args.status,
            log_list=args.log_list,
        )

    if args.command == "schedule":
        return run_schedule(args.platform, install=args.install)

    if args.command == "init-config":
        return run_init_config(target=args.output, force=args.force)

    if args.command == "organize":
        return run_organize(args.output_root)

    if args.command == "migrate":
        return run_migrate(
            args.output_root,
            apply=args.apply,
            manifest_path=args.manifest,
            backup_dir=args.backup_dir,
            rollback_from=args.rollback,
        )

    written = run_backfill(args.output_root)
    print(f"Backfilled {len(written)} sidecars under {args.output_root}")
    for path in written:
        print(path.as_posix())
    return 0


def console_main() -> None:
    raise SystemExit(main())
