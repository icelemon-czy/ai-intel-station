from __future__ import annotations

import html
import xml.etree.ElementTree as ET
from pathlib import Path
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from ai_intel_station.library.archive_paths import arxiv_identity, paper_leaf
from ai_intel_station.library.items import build_paper_item, write_research_item


ROOT_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT_DIR / "output" / "papers"
ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_ATOM_FEED = "https://rss.arxiv.org/atom/{category}"
ARXIV_REQUEST_TIMEOUT_SECONDS = 15
ARXIV_MAX_ATTEMPTS = 2
ARXIV_RETRY_DELAY_SECONDS = 3
ARXIV_MAX_RETRY_AFTER_SECONDS = 30
ARXIV_RESPONSE_CAP_BYTES = 5 * 1024 * 1024

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


class PapersFetchError(RuntimeError):
    """A category fetch failed before a valid arXiv response was available."""


def _is_retryable_fetch_error(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        # A throttled search API switches immediately to the separate
        # official daily feed instead of spending another rate-limited call.
        return 500 <= exc.code < 600
    return isinstance(exc, (URLError, TimeoutError, ConnectionError, OSError))


def _retry_delay_seconds(exc: Exception) -> int:
    if isinstance(exc, HTTPError) and exc.headers is not None:
        retry_after = exc.headers.get("Retry-After")
        if retry_after is not None:
            try:
                return min(
                    ARXIV_MAX_RETRY_AFTER_SECONDS,
                    max(0, int(retry_after)),
                )
            except (TypeError, ValueError):
                pass
    return ARXIV_RETRY_DELAY_SECONDS


def _request_headers() -> dict[str, str]:
    return {
        # arXiv recommends identifying clients; a missing User-Agent has
        # historically produced 403s.
        "User-Agent": "ai-intel-station/0.1 (research workspace; +https://github.com/example/ai-intel-station)",
        # Some arXiv/proxy paths leave a keep-alive response open after
        # sending the Atom body. Closing this one-shot request makes
        # end-of-body observable without abandoning HTTPS.
        "Connection": "close",
    }


def _read_arxiv_response(
    request: Request,
    *,
    category: str,
    max_attempts: int,
) -> tuple[bytes, str | None]:
    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(
                request,
                timeout=ARXIV_REQUEST_TIMEOUT_SECONDS,
            ) as response:
                return (
                    response.read(ARXIV_RESPONSE_CAP_BYTES),
                    response.headers.get("Content-Length"),
                )
        except Exception as exc:
            final_attempt = attempt >= max_attempts
            if final_attempt or not _is_retryable_fetch_error(exc):
                raise
            delay = _retry_delay_seconds(exc)
            print(
                f"  ↻ transient arXiv error for {category}: {exc}; "
                f"retrying in {delay}s"
            )
            sleep(delay)
    raise AssertionError("arXiv retry loop exited without a response")


def fetch_papers_by_category(
    categories: list[str],
    max_results: int = 10,
    *,
    raise_on_error: bool = False,
) -> list[dict]:
    papers = []

    for category in categories:
        if category not in AI_CATEGORIES:
            message = f"Unknown category: {category}"
            print(f"⚠️  {message}")
            if raise_on_error:
                raise PapersFetchError(message)
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
            request = Request(url, headers=_request_headers())
            try:
                raw, content_length = _read_arxiv_response(
                    request,
                    category=category,
                    max_attempts=ARXIV_MAX_ATTEMPTS,
                )
            except Exception as api_exc:
                fallback_url = ARXIV_ATOM_FEED.format(category=category)
                print(
                    f"  ↳ arXiv search API unavailable for {category}: {api_exc}; "
                    "using official Atom feed"
                )
                fallback_request = Request(
                    fallback_url,
                    headers=_request_headers(),
                )
                try:
                    raw, content_length = _read_arxiv_response(
                        fallback_request,
                        category=category,
                        max_attempts=1,
                    )
                except Exception as fallback_exc:
                    raise RuntimeError(
                        f"search API failed ({api_exc}); "
                        f"official Atom feed failed ({fallback_exc})"
                    ) from fallback_exc

            # If the response indicates more data (Content-Length larger
            # than our cap, or the read() returned the full cap meaning the
            # server probably had more), refuse to parse an incomplete feed.
            too_big_from_header = False
            if content_length is not None:
                try:
                    too_big_from_header = (
                        int(content_length) > ARXIV_RESPONSE_CAP_BYTES
                    )
                except ValueError:
                    pass
            truncated = (
                too_big_from_header or len(raw) >= ARXIV_RESPONSE_CAP_BYTES
            )
            if truncated:
                message = (
                    f"arXiv response for {category} "
                    f"({'header' if too_big_from_header else 'truncated-buffer'} "
                    f"exceeds {ARXIV_RESPONSE_CAP_BYTES}-byte cap)"
                )
                print(f"⚠️  {message}; skipping")
                if raise_on_error:
                    raise PapersFetchError(message)
                continue
            xml_content = raw.decode("utf-8")

            root = ET.fromstring(xml_content)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", ns)[:max_results]:
                paper = parse_atom_entry(entry, ns)
                # Skip entries that yielded nothing usable — a row
                # with no title and no arxiv id is about-the-format
                # garbage that the API occasionally returns.
                if not (paper["title"] or paper["arxiv_id"]):
                    continue
                papers.append(paper)
                print(f"  ✅ {paper['title'][:60]}...")
        except PapersFetchError:
            raise
        except Exception as exc:
            message = f"Failed to fetch {category}: {exc}"
            print(f"  ❌ {message}")
            if raise_on_error:
                raise PapersFetchError(message) from exc

    return papers


def fetch_papers_by_query(
    query: str,
    max_results: int = 10,
    *,
    raise_on_error: bool = False,
) -> list[dict]:
    """Fetch arXiv papers matching a keyword query (``search_query=all:"<query>"``).

    Shares the request headers, retry loop, response-cap guard and Atom parser
    with :func:`fetch_papers_by_category`; only the query string differs and the
    ``sort`` is relevance rather than ``submittedDate``. There is deliberately no
    per-category daily Atom fallback here — that feed is category-scoped, so a
    keyword sweep relies on the search API alone and surfaces a failure to the
    caller. Used by Interest Sweep; it never changes the ``collect papers`` CLI.
    """
    query = (query or "").strip()
    if not query:
        message = "arXiv query fetch requires a non-empty query"
        print(f"⚠️  {message}")
        if raise_on_error:
            raise PapersFetchError(message)
        return []

    params = urlencode(
        {
            "search_query": f'all:"{query}"',
            "sortBy": "relevance",
            "sortOrder": "descending",
            "max_results": max_results,
        }
    )
    url = f"{ARXIV_API}?{params}"
    print(f"🔎 Fetching arXiv query {query!r}...")

    try:
        request = Request(url, headers=_request_headers())
        raw, content_length = _read_arxiv_response(
            request,
            category=f"query:{query}",
            max_attempts=ARXIV_MAX_ATTEMPTS,
        )
        too_big_from_header = False
        if content_length is not None:
            try:
                too_big_from_header = int(content_length) > ARXIV_RESPONSE_CAP_BYTES
            except ValueError:
                pass
        if too_big_from_header or len(raw) >= ARXIV_RESPONSE_CAP_BYTES:
            message = (
                f"arXiv query response for {query!r} exceeds "
                f"{ARXIV_RESPONSE_CAP_BYTES}-byte cap"
            )
            print(f"⚠️  {message}; skipping")
            if raise_on_error:
                raise PapersFetchError(message)
            return []
        root = ET.fromstring(raw.decode("utf-8"))
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers: list[dict] = []
        for entry in root.findall("atom:entry", ns)[:max_results]:
            paper = parse_atom_entry(entry, ns)
            if not (paper["title"] or paper["arxiv_id"]):
                continue
            papers.append(paper)
            print(f"  ✅ {paper['title'][:60]}...")
        return papers
    except PapersFetchError:
        raise
    except Exception as exc:
        message = f"Failed to fetch arXiv query {query!r}: {exc}"
        print(f"  ❌ {message}")
        if raise_on_error:
            raise PapersFetchError(message) from exc
        return []


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
        text = el.text.strip()
        if not text:
            return None
        # arxiv Atom ids come in three shapes:
        #   oai:arxiv.org/oai:math.GT/1234
        #   http://arxiv.org/abs/2606.00001v1
        #   tag:arxiv.org:2002:math.GT/1234
        # The arxiv id is the trailing path component after a slash.
        # Reject anything that still carries a URN/URI prefix
        # (i.e. has a `:` before the trailing component) — those are
        # the wrapping feed ids, not the paper id.
        if ":" in text.rsplit("/", 1)[-1]:
            return None
        tail = text.rsplit("/", 1)[-1].strip()
        if not tail or not any(ch.isdigit() for ch in tail):
            return None
        return tail

    authors = [
        html.unescape(_text_or_blank(author.find("atom:name", ns))).strip()
        for author in entry.findall("atom:author", ns)
    ]
    if not authors:
        creator = entry.find("{http://purl.org/dc/elements/1.1/}creator")
        creator_text = _text_or_blank(creator)
        authors = [
            html.unescape(name).strip()
            for name in creator_text.split(",")
            if name.strip()
        ]

    paper = {
        "title": html.unescape(_text_or_blank(title_el)).strip().replace("\n", " "),
        "authors": authors,
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

    if paper["arxiv_id"] is None and paper["abs_url"]:
        candidate = paper["abs_url"].rstrip("/").rsplit("/", 1)[-1]
        if candidate and any(char.isdigit() for char in candidate):
            paper["arxiv_id"] = candidate
    if paper["pdf_url"] is None and paper["arxiv_id"]:
        paper["pdf_url"] = f"https://arxiv.org/pdf/{paper['arxiv_id']}"

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
    """Persist each paper at ``output/papers/<arxiv-id>.md``.

    ``category`` is only provenance (a cross-listed paper is stored once under
    its stable ``arxiv-id``); the same id collected from another category writes
    to the same path, so cross-category copies self-merge instead of duplicating.
    ``output_dir`` is the papers source root (``output/papers``).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    from ai_intel_station.library.items import _atomic_write_text

    saved = 0
    for index, paper in enumerate(papers):
        # Defensive: a malformed arxiv response missing the title field still
        # gets a placeholder so the abstract and id remain inspectable.
        title = paper.get("title") or f"untitled-{index + 1:02d}"
        arxiv_id = arxiv_identity(paper.get("abs_url"), title)
        filepath = output_dir / paper_leaf(arxiv_id)
        body = paper_to_markdown(paper)
        # Atomic write — see library.items._atomic_write_text for the rationale.
        _atomic_write_text(filepath, body)
        sidecar_path = output_dir / paper_leaf(arxiv_id, suffix=".research-item.json")
        item = build_paper_item(paper, filepath)
        # If the same arXiv identity was already collected from another category,
        # keep the union of categories/tags as provenance instead of dropping them.
        item.tags = _union_categories(sidecar_path, item.tags)
        write_research_item(item, sidecar_path)
        saved += 1

    print(f"✅ Saved {saved} papers to {output_dir} (identity: arxiv-id)")


def _union_categories(sidecar_path: Path, current_tags: list[str]) -> list[str]:
    import json

    try:
        existing = json.loads(Path(sidecar_path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeDecodeError):
        existing = None
    prior = existing.get("tags") if isinstance(existing, dict) else None
    if not isinstance(prior, list):
        return sorted(set(current_tags))
    return sorted(set(current_tags) | {str(t) for t in prior})
