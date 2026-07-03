from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _atomic_write_text(path: Path, content: str) -> None:
    """Atomically write ``content`` to ``path`` via tempfile + rename.

    A direct ``path.write_text`` either keeps the old file (SIGTERM
    before open) or writes a half-truncated file (SIGTERM mid-write).
    Downstream library readers parse such half-files as corrupted
    sidecars and silently drop them, which is hard to diagnose.

    The atomic alternative is: write to a sibling .tmp file, fsync,
    os.replace. The new file is either complete and visible, or the
    old file is intact and the .tmp file is left as garbage.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise


@dataclass
class ResearchItem:
    source: str
    item_type: str
    title: str
    canonical_url: str | None = None
    summary: str | None = None
    authors: list[str] = field(default_factory=list)
    published_at: str | None = None
    updated_at: str | None = None
    tags: list[str] = field(default_factory=list)
    output_path: str | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.source = self.source.strip()
        self.item_type = self.item_type.strip()
        self.title = self.title.strip()
        self.canonical_url = _clean_text(self.canonical_url)
        self.summary = _clean_text(self.summary)
        self.authors = _clean_list(self.authors)
        self.published_at = _clean_text(self.published_at)
        self.updated_at = _clean_text(self.updated_at)
        self.tags = _clean_list(self.tags)
        self.output_path = _normalize_output_path(self.output_path)
        self.metadata = {
            key: value
            for key, value in (self.metadata or {}).items()
            if value not in (None, "", [], {})
        }

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        # No indent — JSON sidecars are loaded per-file by load_research_items
        # and pretty-printing doubles file size + parse time for no benefit.
        return json.dumps(self.to_dict(), ensure_ascii=False)


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_list(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []

    cleaned = []
    for value in values:
        text = _clean_text(value)
        if text:
            cleaned.append(text)
    return cleaned


def _normalize_output_path(path: str | Path | None) -> str | None:
    """Normalize ``path`` to a string relative to ``REPO_ROOT`` when possible.

    Three input shapes collapse to ``None``:
      - ``None`` (caller passed no path)
      - empty string (often used as a "no path" sentinel)
      - whitespace-only (after stripping becomes empty)

    Collapsing whitespace-only paths to ``None`` is what makes the
    ``filter value not in (None, "", [], {})`` short-circuit in
    ``__post_init__`` consistent: a path that was set but never written
    is treated the same as no path at all.
    """
    if path is None:
        return None
    text = str(path).strip()
    if not text:
        return None

    path_obj = Path(text)
    if path_obj.is_absolute():
        try:
            path_obj = path_obj.relative_to(REPO_ROOT)
        except ValueError:
            pass

    normalized = path_obj.as_posix()
    return normalized or None


def _split_csv(value: str | None) -> list[str]:
    if not value:
        return []

    return [part.strip() for part in value.split(",") if part.strip()]


def _github_owner_repo_from_url(url: str | None) -> tuple[str | None, str | None]:
    if not url:
        return None, None

    match = re.match(r"https://github\.com/([^/]+)/([^/]+?)/?$", url.strip())
    if not match:
        return None, None

    return match.group(1), match.group(2)


def _first_content_paragraph(lines: list[str]) -> str | None:
    paragraph = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped == "---":
            if paragraph:
                break
            continue
        paragraph.append(stripped)

    return _clean_text(" ".join(paragraph))


def build_github_repo_item(owner: str, repo: str, data: dict, markdown_path: Path) -> ResearchItem:
    topics = [
        topic["topic"]["name"]
        for topic in data.get("repositoryTopics", [])
        if topic.get("topic", {}).get("name")
    ]
    return ResearchItem(
        source="github",
        item_type="repository",
        title=data.get("name") or repo,
        canonical_url=data.get("url"),
        summary=data.get("description"),
        published_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        tags=topics,
        output_path=markdown_path,
        metadata={
            "owner": owner,
            "repo": repo,
            "stargazer_count": data.get("stargazerCount"),
            "primary_language": data.get("primaryLanguage", {}).get("name"),
            "issue_count": len(data.get("issues", [])),
        },
    )


def build_github_search_items(query: str, repos: list[dict], markdown_path: Path) -> list[ResearchItem]:
    items = []
    for repo in repos:
        owner = repo.get("owner", {}).get("login")
        parsed_owner, parsed_repo = _github_owner_repo_from_url(repo.get("url"))
        items.append(
            ResearchItem(
                source="github",
                item_type="search-result",
                title=repo.get("name") or parsed_repo or "unknown",
                canonical_url=repo.get("url"),
                summary=repo.get("description"),
                output_path=markdown_path,
                metadata={
                    "query": query,
                    "owner": owner or parsed_owner,
                    "repo": repo.get("name") or parsed_repo,
                    "stargazer_count": repo.get("stargazersCount") or repo.get("stargazerCount"),
                },
            )
        )

    return items


def build_paper_item(paper: dict, markdown_path: Path) -> ResearchItem:
    return ResearchItem(
        source="papers",
        item_type="paper",
        title=paper.get("title") or "Untitled paper",
        canonical_url=paper.get("abs_url"),
        summary=paper.get("summary"),
        authors=paper.get("authors") or [],
        published_at=paper.get("published"),
        tags=paper.get("categories") or [],
        output_path=markdown_path,
        metadata={
            "pdf_url": paper.get("pdf_url"),
        },
    )


def build_wechat_item(meta: dict, markdown_path: Path, body_markdown: str | None = None) -> ResearchItem:
    author = _clean_text(meta.get("author") or meta.get("publisher"))
    summary = _clean_text(meta.get("summary")) or _first_content_paragraph((body_markdown or "").splitlines())
    return ResearchItem(
        source="wechat",
        item_type="article",
        title=meta.get("title") or markdown_path.stem,
        canonical_url=meta.get("source_url") or meta.get("url"),
        summary=summary,
        authors=[author] if author else [],
        published_at=meta.get("publish_time") or meta.get("published_at"),
        output_path=markdown_path,
        metadata={
            "publisher": author,
            "body_length": len(body_markdown or ""),
        },
    )


def write_research_item(item: ResearchItem, output_path: Path) -> Path:
    """Atomically write a single ResearchItem sidecar.

    Uses tempfile + os.replace so a process crash mid-write cannot leave
    a half-written JSON file that subsequent library reads would treat
    as corrupted sidecar data. No trailing newline — JSON sidecars
    are line-delimited and ``load_research_items`` splits by ``}\n{``.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(output_path, item.to_json())
    return output_path


def write_research_items_jsonl(items: list[ResearchItem], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        json.dumps(item.to_dict(), ensure_ascii=False) for item in items
    )
    if body:
        body += "\n"
    _atomic_write_text(output_path, body)
    return output_path


def parse_github_repo_markdown(markdown_path: Path) -> ResearchItem:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    # Skip leading blank lines so a file that starts with a BOM
    # artefact or a leading newline pair still picks up the real H1.
    # The previous code indexed lines[0] directly, which produced an
    # empty title for any file with a leading blank line.
    title_index = 0
    while title_index < len(lines) and not lines[title_index].strip():
        title_index += 1
    raw_title = lines[title_index].strip() if title_index < len(lines) else ""
    # Accept any leading `#` / `##` / `###` heading — gh writes the
    # repo description as a single `#` heading, but a hand-edit
    # might use a deeper level. The previous code matched only
    # `# ` (single hash + space), so `## title` came through as
    # `## title` with the leading `##` left in place.
    title = raw_title
    for prefix in ("### ", "## ", "# "):
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    title = title.strip()
    summary_lines = []
    index = title_index + 1
    while index < len(lines):
        line = lines[index]
        if line.startswith("> "):
            summary_lines.append(line[2:].strip())
            index += 1
            continue
        if summary_lines or line.startswith("- "):
            break
        index += 1

    url = None
    created = None
    updated = None
    language = None
    stars = None
    tags = []
    issue_count = 0
    in_topics = False
    in_issues = False

    for line in lines:
        # Normalise: strip trailing whitespace, collapse runs of
        # spaces inside the heading, and ignore case so '## Topics',
        # '## topics', and '##  Topics  ' all match. Real markdown
        # files frequently have inconsistent heading formatting
        # after a `gh repo view` round-trip.
        normalised_heading = " ".join(line.rstrip().split()).lower()
        if normalised_heading == "## topics":
            in_topics = True
            in_issues = False
            continue
        if normalised_heading == "## open issues":
            in_topics = False
            in_issues = True
            continue
        if line.startswith("## "):
            in_topics = False
            in_issues = False
        if in_topics and line.startswith("- `") and line.endswith("`"):
            tags.append(line[3:-1])
            continue
        if in_issues and line.startswith("- [#"):
            issue_count += 1
            continue
        if line.startswith("- ⭐ Stars: "):
            try:
                stars = int(line.removeprefix("- ⭐ Stars: ").strip())
            except ValueError:
                # The "Stars:" line is hand-edited; tolerate a
                # non-numeric value (e.g. 'n/a') by leaving stars
                # as None rather than crashing the whole parser.
                stars = None
        elif line.startswith("- 🏷️ Language: "):
            language = _clean_text(line.removeprefix("- 🏷️ Language: "))
        elif line.startswith("- 🌐 URL: "):
            url = _clean_text(line.removeprefix("- 🌐 URL: "))
        elif line.startswith("- 📅 Created: "):
            created = _clean_text(line.removeprefix("- 📅 Created: "))
        elif line.startswith("- 🔄 Updated: "):
            updated = _clean_text(line.removeprefix("- 🔄 Updated: "))

    owner, repo = _github_owner_repo_from_url(url)
    return ResearchItem(
        source="github",
        item_type="repository",
        title=title,
        canonical_url=url,
        summary=" ".join(summary_lines),
        published_at=created,
        updated_at=updated,
        tags=tags,
        output_path=markdown_path,
        metadata={
            "owner": owner,
            "repo": repo,
            "stargazer_count": stars,
            "primary_language": language,
            "issue_count": issue_count,
        },
    )


def parse_github_search_markdown(markdown_path: Path) -> list[ResearchItem]:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    query = lines[0].removeprefix("# Search: ").strip()
    items = []

    index = 0
    while index < len(lines):
        match = re.match(r"## \[(.+?)\]\((https://github\.com/[^)]+)\)$", lines[index])
        if not match:
            index += 1
            continue

        title = match.group(1)
        url = match.group(2)
        stars = None
        description = None

        if index + 1 < len(lines) and lines[index + 1].startswith("- ⭐ "):
            star_text = lines[index + 1].removeprefix("- ⭐ ").removesuffix(" stars").strip()
            if star_text.isdigit():
                stars = int(star_text)
        if index + 2 < len(lines) and lines[index + 2].startswith("- "):
            description = lines[index + 2].removeprefix("- ").strip()

        owner, repo = _github_owner_repo_from_url(url)
        items.append(
            ResearchItem(
                source="github",
                item_type="search-result",
                title=title,
                canonical_url=url,
                summary=description,
                output_path=markdown_path,
                metadata={
                    "query": query,
                    "owner": owner,
                    "repo": repo,
                    "stargazer_count": stars,
                },
            )
        )
        index += 3

    return items


def _parse_paper_authors(authors_line: str) -> tuple[list[str], int | None]:
    total_match = re.search(r"\((\d+) authors total\)$", authors_line)
    total_authors = int(total_match.group(1)) if total_match else None
    cleaned = re.sub(r" et al\. \(\d+ authors total\)$", "", authors_line).strip()
    return _split_csv(cleaned), total_authors


def parse_paper_markdown(markdown_path: Path) -> ResearchItem:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    authors_line = next(
        (line.removeprefix("> **Authors:** ").strip() for line in lines if line.startswith("> **Authors:** ")),
        "",
    )
    authors, total_authors = _parse_paper_authors(authors_line)
    published = next((line.removeprefix("- 📅 Published: ").strip() for line in lines if line.startswith("- 📅 Published: ")), None)
    categories = next((line.removeprefix("- 🏷️ Categories: ").strip() for line in lines if line.startswith("- 🏷️ Categories: ")), "")
    abs_url = next((line.removeprefix("- 🔗 arXiv: ").strip() for line in lines if line.startswith("- 🔗 arXiv: ")), None)
    pdf_url = next((line.removeprefix("- 📄 PDF: ").strip() for line in lines if line.startswith("- 📄 PDF: ")), None)

    abstract_index = next((i for i, line in enumerate(lines) if line == "## Abstract"), None)
    abstract = None
    if abstract_index is not None:
        abstract = "\n".join(lines[abstract_index + 2:]).strip()

    return ResearchItem(
        source="papers",
        item_type="paper",
        title=title,
        canonical_url=abs_url,
        summary=abstract,
        authors=authors,
        published_at=published,
        tags=_split_csv(categories),
        output_path=markdown_path,
        metadata={
            "pdf_url": pdf_url,
            "authors_total": total_authors,
        },
    )


def parse_wechat_markdown(markdown_path: Path) -> ResearchItem:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    author = None
    published = None
    source_url = None
    body_lines = []
    body_started = False

    for line in lines[1:]:
        if not body_started and line.strip() == "---":
            body_started = True
            continue
        if not body_started:
            if line.startswith("> 公众号: "):
                author = line.removeprefix("> 公众号: ").strip()
            elif line.startswith("> 发布时间: "):
                published = line.removeprefix("> 发布时间: ").strip()
            elif line.startswith("> 原文链接: "):
                source_url = line.removeprefix("> 原文链接: ").strip()
            continue

        body_lines.append(line)

    return ResearchItem(
        source="wechat",
        item_type="article",
        title=title,
        canonical_url=source_url,
        summary=_first_content_paragraph(body_lines),
        authors=[author] if author else [],
        published_at=published,
        output_path=markdown_path,
        metadata={
            "publisher": author,
        },
    )


def _backfill_github(output_root: Path) -> list[Path]:
    written = []
    github_root = output_root / "github"
    if not github_root.exists():
        return written

    for item_dir in sorted(path for path in github_root.iterdir() if path.is_dir()):
        repo_markdown = item_dir / "README.md"
        search_markdown = item_dir / "search.md"

        if repo_markdown.exists():
            repo_item = parse_github_repo_markdown(repo_markdown)
            written.append(write_research_item(repo_item, item_dir / "research-item.json"))

        if search_markdown.exists():
            search_items = parse_github_search_markdown(search_markdown)
            written.append(write_research_items_jsonl(search_items, item_dir / "research-items.jsonl"))

    return written


def _backfill_papers(output_root: Path) -> list[Path]:
    written = []
    papers_root = output_root / "papers"
    if not papers_root.exists():
        return written

    for markdown_path in sorted(papers_root.rglob("*.md")):
        paper_item = parse_paper_markdown(markdown_path)
        sidecar_path = markdown_path.with_name(f"{markdown_path.stem}.research-item.json")
        written.append(write_research_item(paper_item, sidecar_path))

    return written


def _backfill_wechat(output_root: Path) -> list[Path]:
    written = []
    wechat_root = output_root / "wechat"
    if not wechat_root.exists():
        return written

    for article_dir in sorted(path for path in wechat_root.iterdir() if path.is_dir()):
        article_markdown = next((path for path in sorted(article_dir.glob("*.md")) if path.is_file()), None)
        if article_markdown is None:
            continue
        article_item = parse_wechat_markdown(article_markdown)
        written.append(write_research_item(article_item, article_dir / "research-item.json"))

    return written


def backfill_output_tree(output_root: Path) -> list[Path]:
    output_root = Path(output_root)
    written = []
    written.extend(_backfill_github(output_root))
    written.extend(_backfill_papers(output_root))
    written.extend(_backfill_wechat(output_root))
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill ResearchItem sidecars for existing output artifacts")
    parser.add_argument(
        "output_root",
        nargs="?",
        type=Path,
        default=REPO_ROOT / "output",
        help="Existing output root to scan (default: ./output)",
    )
    args = parser.parse_args()

    written = backfill_output_tree(args.output_root)
    print(f"Backfilled {len(written)} sidecars under {args.output_root}")
    for path in written:
        print(_normalize_output_path(path) or path.as_posix())


if __name__ == "__main__":
    main()
