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
                # larger than our cap, or the read() returned the
                # full cap meaning the server probably had more),
                # refuse to parse — the result would be incomplete
                # and the user has no signal for it.
                content_length = response.headers.get("Content-Length")
                too_big_from_header = False
                if content_length is not None:
                    try:
                        too_big_from_header = int(content_length) > max_bytes
                    except ValueError:
                        pass
                # A chunked / unknown-length response that filled the
                # buffer is also a truncation signal. urlopen does not
                # expose "is EOF" cleanly, but read(N) returning
                # exactly N bytes is suspicious; in practice a
                # well-formed arxiv response is < 1 MB and any
                # exactly-5MB read is suspicious enough to skip.
                truncated = too_big_from_header or len(raw) >= max_bytes
                if truncated:
                    print(
                        f"⚠️  arXiv response for {category} "
                        f"({'header' if too_big_from_header else 'truncated-buffer'} "
                        f"exceeds {max_bytes}-byte cap); skipping"
                    )
                    continue
                xml_content = raw.decode("utf-8")

            root = ET.fromstring(xml_content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns):
                paper = parse_atom_entry(entry, ns)
                # Skip entries that yielded nothing usable — a row
                # with no title and no arxiv id is about-the-format
                # garbage that the API occasionally returns.
                if not (paper["title"] or paper["arxiv_id"]):
                    continue
                papers.append(paper)
                print(f"  ✅ {paper['title'][:60]}...")
        except Exception as exc:
            print(f"  ❌ Failed to fetch {category}: {exc}")

    return papers


def parse_atom_entry(entry, ns=None) -> dict:
    """Convert an arxiv Atom <entry> into the dict shape consumed by
    ``save_papers``.

    Tolerates missing elements — a row without ``<title>`` or
    ``<published>`` used to dereference ``None.text`` and crash
    mid-loop, dropping every paper after the bad row.
    """
    if ns is None:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
    title_el = entry.find("atom:title", ns)
    summary_el = entry.find("atom:summary", ns)
    published_el = entry.find("atom:published", ns)
    updated_el = entry.find("atom:updated", ns)
    id_el = entry.find("atom:id", ns)

    def _text_or_blank(el) -> str:
        """Return ``el.text`` or empty string.

        arXiv Atom feeds sometimes omit fields like ``<published>`` or
        ``<title>`` (the seed schema says they are required but
        mirror sites skip them). Without the guard, ``el.text``
        raises AttributeError mid-loop and aborts the entire
        category fetch — silently dropping every paper after the
        bad row.
        """
        return el.text if (el is not None and el.text is not None) else ""

    def _arxiv_id(el) -> str | None:
        if el is None or el.text is None:
            return None
        return el.text.split("/")[-1]

    paper = {
        "title": html.unescape(_text_or_blank(title_el)).strip().replace("\n", " "),
        "authors": [
            html.unescape(_text_or_blank(author.find("atom:name", ns))).strip()
            for author in entry.findall("atom:author", ns)
        ],
        "summary": html.unescape(_text_or_blank(summary_el)).strip(),
        "published": _text_or_blank(published_el).strip(),
        "updated": _text_or_blank(updated_el).strip(),
        "arxiv_id": _arxiv_id(id_el),
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
        term = category_elem.get("term", "")
        if term:
            paper["categories"].append(term)
    return paper


def paper_to_markdown(paper: dict) -> str:
    # Defensive: a malformed arxiv response can omit authors / title /
    # etc. The previous code raised KeyError for any missing field
    # and aborted the whole save loop. The defaults below keep the
    # operator-facing markdown usable even on a partial payload.
    title = paper.get("title") or "Untitled"
    authors = paper.get("authors") or []
    authors_str = ", ".join(authors[:5])
    if len(authors) > 5:
        authors_str += f" et al. ({len(authors)} authors total)"

    lines = [
        f"# {title}",
        "",
        f"> **Authors:** {authors_str}",
        "",
        f"- 📅 Published: {(paper.get('published') or '')[:10]}",
        f"- 🏷️ Categories: {', '.join((paper.get('categories') or [])[:3])}",
        f"- 🔗 arXiv: {paper.get('abs_url') or 'N/A'}",
        f"- 📄 PDF: {paper.get('pdf_url') or 'N/A'}",
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
        # Defensive: a malformed arxiv response missing the title
        # field would have raised KeyError here. We still want to
        # save the paper so the operator can see what we got, just
        # with a placeholder title.
        title = paper.get("title") or f"untitled-{index + 1:02d}"
        safe_title = "".join(char for char in title[:50] if char.isalnum() or char in " -").strip()
        # If the title is purely punctuation / CJK / unicode that the
        # `isalnum()` filter strips, fall back to a positional name
        # so the file is not named literally ".md".
        if not safe_title:
            safe_title = f"untitled-{index + 1:02d}"
        filepath = category_dir / f"{index + 1:02d}-{safe_title}.md"
        body = paper_to_markdown(paper)
        # Atomic write — see library.items._atomic_write_text for the
        # rationale. A SIGTERM mid-write used to leave a half-written
        # file the operator assumed was complete.
        from library.items import _atomic_write_text
        _atomic_write_text(filepath, body)
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
