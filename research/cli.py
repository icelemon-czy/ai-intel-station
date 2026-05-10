from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from briefing.reports import write_digest_report, write_reading_list_report
from collect.github import run_gh, save_repo, save_search_results
from collect.papers import CATEGORIES_HELP, fetch_papers_by_category, save_papers
from collect.wechat import fetch_article, normalize_wechat_url
from library.items import backfill_output_tree
from library.query import query_research_items


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "output"


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

    briefing_parser = subparsers.add_parser("briefing", help="Generate briefing artifacts from local sidecars")
    briefing_parser.add_argument("mode", choices=["digest", "reading-list"])
    briefing_parser.add_argument("keyword")
    briefing_parser.add_argument("--title")
    briefing_parser.add_argument("--source", action="append", dest="sources")
    briefing_parser.add_argument("--since")
    briefing_parser.add_argument("--until")
    briefing_parser.add_argument("-o", "--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)

    backfill_parser = subparsers.add_parser("backfill", help="Backfill ResearchItem sidecars from historical Markdown")
    backfill_parser.add_argument("output_root", nargs="?", type=Path, default=DEFAULT_OUTPUT_ROOT)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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

    written = run_backfill(args.output_root)
    print(f"Backfilled {len(written)} sidecars under {args.output_root}")
    for path in written:
        print(path.as_posix())
    return 0


def console_main() -> None:
    raise SystemExit(main())
