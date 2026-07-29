from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from briefing.reports import write_digest_report, write_reading_list_report
from collect.github import run_gh, save_repo, save_search_results
from collect.papers import CATEGORIES_HELP, fetch_papers_by_category, save_papers
from collect.wechat import (
    WeChatRuntimeDependencyError,
    fetch_article,
    normalize_wechat_url,
)
from library.items import backfill_output_tree
from library.query import query_research_items
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
    github_root = Path(output_root) / "github"
    if search:
        query = " ".join(targets)
        repos = json.loads(
            run_gh(
                [
                    "search",
                    "repos",
                    query,
                    "--sort",
                    "stars",
                    "--limit",
                    "10",
                    "--json",
                    "name,owner,description,url,stargazersCount",
                ]
            )
        )
        save_search_results(query, github_root, repos)
        return

    for target in targets:
        if "/" not in target:
            print(f"⚠️  Skipping '{target}' - expected format: owner/repo")
            continue
        owner, repo = target.split("/", 1)
        save_repo(owner, repo, github_root)


def collect_paper_categories(categories: list[str], output_root: Path, max_results: int = 10) -> None:
    if not categories:
        print("⚠️  Please specify at least one category. Use --list to see available categories.")
        print(CATEGORIES_HELP)
        return

    papers_root = Path(output_root) / "papers"
    papers = fetch_papers_by_category(categories, max_results)
    if not papers:
        return

    for category in categories:
        category_papers = [paper for paper in papers if category in paper.get("categories", [])]
        if category_papers:
            save_papers(category_papers, category, papers_root)


async def collect_wechat_article(url: str, output_root: Path) -> None:
    normalized = normalize_wechat_url(url)
    if not normalized.startswith("https://mp.weixin.qq.com/"):
        raise ValueError("Expected an mp.weixin.qq.com article URL")
    await fetch_article(normalized, output_dir=Path(output_root) / "wechat")


def render_query_results(output_root: Path, keyword: str, sources: list[str] | None, since: str | None, until: str | None) -> str:
    items = query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
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
    for section in ("digests", "reading-lists"):
        section_dir = briefing_root / section
        if section_dir.exists():
            found.extend(sorted(section_dir.glob("*.md"), reverse=True))
    if not found:
        print(f"📭 No briefing markdown found under {briefing_root}.")
        return 0

    output_root = Path(output_root).resolve()
    print(f"📰 {len(found)} briefing file(s) under {briefing_root}:")
    for path in found:
        try:
            rel = path.relative_to(output_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        print(f"  • {rel}")
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
    items = query_research_items(output_root, keyword=keyword, sources=sources, since=since, until=until)
    final_title = title or keyword
    if mode == "digest":
        return write_digest_report(output_root, title=final_title, items=items, requested_sources=sources)
    return write_reading_list_report(output_root, title=final_title, items=items, requested_sources=sources)


def run_backfill(output_root: Path) -> list[Path]:
    return backfill_output_tree(output_root)


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
    return 0 if not any(r.failed for r in report.sources.values()) else 1


VALID_SOURCES = ("github", "papers", "wechat")


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

    web_parser = subparsers.add_parser("web", help="Launch the local web workspace")
    web_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    discover_parser = subparsers.add_parser(
        "discover",
        help="Run the configured daily discovery sweep (GitHub + arXiv + WeChat + briefing)",
        epilog=(
            "First time? Run these in order:\n"
            "  uv run research init-config\n"
            "  uv run research discover --dry-run\n"
            "  uv run research discover\n"
            "See docs/daily-discovery.md for the full guide."
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
        help="Limit the sweep to one or more sources (repeatable, or comma-separated)",
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

    written = run_backfill(args.output_root)
    print(f"Backfilled {len(written)} sidecars under {args.output_root}")
    for path in written:
        print(path.as_posix())
    return 0


def console_main() -> None:
    raise SystemExit(main())
