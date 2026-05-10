from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from briefing.reports import write_digest_report, write_reading_list_report
from library.query import query_research_items
from publish.cli import print_saved


OUTPUT_ROOT = REPO_ROOT / "output"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Obsidian-friendly briefings from local research archives")
    parser.add_argument("mode", choices=["digest", "reading-list"])
    parser.add_argument("keyword", help="Keyword used to search the local research library")
    parser.add_argument("--title", help="Optional custom briefing title")
    parser.add_argument("--source", action="append", dest="sources", help="Restrict briefing to one or more sources")
    parser.add_argument("--since", help="Optional lower time bound (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--until", help="Optional upper time bound (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("-o", "--output-root", type=Path, default=OUTPUT_ROOT)
    args = parser.parse_args()

    items = query_research_items(
        args.output_root,
        keyword=args.keyword,
        sources=args.sources,
        since=args.since,
        until=args.until,
    )
    title = args.title or args.keyword
    if args.mode == "digest":
        saved = write_digest_report(args.output_root, title=title, items=items, requested_sources=args.sources)
    else:
        saved = write_reading_list_report(args.output_root, title=title, items=items, requested_sources=args.sources)

    print_saved(saved)


if __name__ == "__main__":
    main()
