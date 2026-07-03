from __future__ import annotations

import argparse
import html
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from library.items import build_paper_item, write_research_item


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "output" / "papers"
ARXIV_API = "https://export.arxiv.org/api/query"

AI_CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language",
    "cs.CV": "Computer Vision",
    "cs.MA": "Multiagent Systems",
    "cs.RO": "Robotics",
    "cs.IR": "Information Retrieval",
    "cs.NE": "Neural and Evolutionary Computing",
}

CATEGORIES_HELP = """
AI-related categories:
  cs.AI  - Artificial Intelligence
  cs.LG  - Machine Learning
  cs.CL  - Computation and Language
  cs.CV  - Computer Vision
  cs.MA  - Multiagent Systems
  cs.RO  - Robotics
  cs.IR  - Information Retrieval
  cs.NE  - Neural and Evolutionary Computing
"""


def fetch_papers_by_category(categories: list[str], max_results: int = 10) -> list[dict]:
    papers = []

    for category in categories:
        if category not in AI_CATEGORIES:
            print(f"⚠️  Unknown category: {category}")
            continue

        params = urlencode(
            {
                "search_query": f"cat:{category}",
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": max_results,
            }
        )
        url = f"{ARXIV_API}?{params}"
        print(f"📚 Fetching {category} ({AI_CATEGORIES[category]})...")

        try:
            request = Request(
                url,
                headers={
                    # arXiv recommends identifying clients; a missing
                    # User-Agent has historically produced 403s.
                    "User-Agent": "ai-intel-station/0.1 (research workspace; +https://github.com/example/ai-intel-station)",
                },
            )
            with urlopen(request, timeout=30) as response:
                # Cap the read at 5 MB so a misbehaving or hostile
                # server cannot stream unlimited content into our
                # memory while the parser is busy.
                max_bytes = 5 * 1024 * 1024
                raw = response.read(max_bytes)
                # If the response indicates more data (Content-Length
                # larger than our cap), refuse to parse — the result
                # would be incomplete and the user has no signal for it.
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        if int(content_length) > max_bytes:
                            print(
                                f"⚠️  arXiv response {content_length} bytes exceeds "
                                f"{max_bytes}-byte cap for category {category}; skipping"
                            )
                            continue
                    except ValueError:
                        pass
                xml_content = raw.decode("utf-8")

            root = ET.fromstring(xml_content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                paper = {
                    "title": html.unescape(entry.find("atom:title", ns).text or "").strip().replace("\n", " "),
                    "authors": [author.find("atom:name", ns).text or "" for author in entry.findall("atom:author", ns)],
                    "summary": html.unescape(entry.find("atom:summary", ns).text or "").strip(),
                    "published": entry.find("atom:published", ns).text or "",
                    "updated": entry.find("atom:updated", ns).text or "",
                    "arxiv_id": entry.find("atom:id", ns).text.split("/")[-1] if entry.find("atom:id", ns) is not None else None,
                    "pdf_url": None,
                    "abs_url": None,
                    "categories": [],
                }

                for link in entry.findall("atom:link", ns):
                    if link.get("title") == "pdf":
                        paper["pdf_url"] = link.get("href")
                    elif link.get("rel") == "alternate" and link.get("type") == "text/html":
                        paper["abs_url"] = link.get("href")

                for category_elem in entry.findall("atom:category", ns):
                    paper["categories"].append(category_elem.get("term", ""))

                papers.append(paper)
                print(f"  ✅ {paper['title'][:60]}...")
        except Exception as exc:
            print(f"  ❌ Failed to fetch {category}: {exc}")

    return papers


def paper_to_markdown(paper: dict) -> str:
    authors_str = ", ".join(paper["authors"][:5])
    if len(paper["authors"]) > 5:
        authors_str += f" et al. ({len(paper['authors'])} authors total)"

    lines = [
        f"# {paper['title']}",
        "",
        f"> **Authors:** {authors_str}",
        "",
        f"- 📅 Published: {paper['published'][:10]}",
        f"- 🏷️ Categories: {', '.join(paper['categories'][:3])}",
        f"- 🔗 arXiv: {paper['abs_url'] or 'N/A'}",
        f"- 📄 PDF: {paper['pdf_url'] or 'N/A'}",
        "",
        "## Abstract",
        "",
        paper["summary"],
        "",
    ]
    return "\n".join(lines)


def save_papers(papers: list[dict], category: str, output_dir: Path) -> None:
    category_dir = output_dir / f"arXiv-{category}"
    category_dir.mkdir(parents=True, exist_ok=True)

    for index, paper in enumerate(papers):
        safe_title = "".join(char for char in paper["title"][:50] if char.isalnum() or char in " -").strip()
        filepath = category_dir / f"{index + 1:02d}-{safe_title}.md"
        filepath.write_text(paper_to_markdown(paper), encoding="utf-8")
        write_research_item(build_paper_item(paper, filepath), filepath.with_name(f"{filepath.stem}.research-item.json"))

    print(f"✅ Saved {len(papers)} papers to {category_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch papers from arXiv by category")
    parser.add_argument("categories", nargs="*", help="arXiv categories (e.g., cs.AI cs.LG)")
    parser.add_argument("--max", type=int, default=10, help="Max papers per category (default: 10)")
    parser.add_argument("--list", action="store_true", help="List AI-related categories")
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()

    if args.list:
        print(CATEGORIES_HELP)
        return
    if not args.categories:
        print("⚠️  Please specify at least one category. Use --list to see available categories.")
        print(CATEGORIES_HELP)
        return

    papers = fetch_papers_by_category(args.categories, args.max)
    if papers:
        for category in args.categories:
            category_papers = [paper for paper in papers if category in paper.get("categories", [])]
            if category_papers:
                save_papers(category_papers, category, args.output)


if __name__ == "__main__":
    main()
