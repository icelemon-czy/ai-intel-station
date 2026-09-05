from __future__ import annotations

import re
from pathlib import Path

from ai_intel_station.library.items import (
    ResearchItem,
    _clean_text,
    _first_content_paragraph,
    _github_owner_repo_from_url,
    _split_csv,
    write_research_item,
    write_research_items_jsonl,
)


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
    # Empty file used to raise IndexError on lines[0]. A search
    # markdown without a `# Search: ` heading carries no per-repo
    # entries, so returning an empty list is the right behaviour.
    if not lines:
        return []
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
        created = None
        updated = None

        if index + 1 < len(lines) and lines[index + 1].startswith("- ⭐ "):
            star_text = lines[index + 1].removeprefix("- ⭐ ").removesuffix(" stars").strip()
            if star_text.isdigit():
                stars = int(star_text)
        if index + 2 < len(lines) and lines[index + 2].startswith("- "):
            description = lines[index + 2].removeprefix("- ").strip()
        block_end = index + 3
        while block_end < len(lines) and not lines[block_end].startswith("## "):
            line = lines[block_end]
            if line.startswith("- 📅 Created: "):
                created = _clean_text(line.removeprefix("- 📅 Created: "))
            elif line.startswith("- 🔄 Updated: "):
                updated = _clean_text(line.removeprefix("- 🔄 Updated: "))
            block_end += 1

        owner, repo = _github_owner_repo_from_url(url)
        items.append(
            ResearchItem(
                source="github",
                item_type="search-result",
                title=title,
                canonical_url=url,
                summary=description,
                published_at=created,
                updated_at=updated,
                output_path=markdown_path,
                signal_role="evidence",
                discovery_method="github-repository-search",
                metadata={
                    "query": query,
                    "owner": owner,
                    "repo": repo,
                    "stargazer_count": stars,
                },
            )
        )
        index = block_end

    return items


def _parse_paper_authors(authors_line: str) -> tuple[list[str], int | None]:
    total_match = re.search(r"\((\d+) authors total\)$", authors_line)
    total_authors = int(total_match.group(1)) if total_match else None
    cleaned = re.sub(r" et al\. \(\d+ authors total\)$", "", authors_line).strip()
    return _split_csv(cleaned), total_authors


def parse_paper_markdown(markdown_path: Path) -> ResearchItem:
    lines = markdown_path.read_text(encoding="utf-8").splitlines()
    # Skip leading blank lines so a file with a leading BOM
    # artefact does not produce an empty title. Accept any heading
    # level (## title, ### title) since a hand-edit might use a
    # deeper level than the canonical # .
    title_index = 0
    while title_index < len(lines) and not lines[title_index].strip():
        title_index += 1
    raw_title = lines[title_index].strip() if title_index < len(lines) else ""
    title = raw_title
    for prefix in ("### ", "## ", "# "):
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    title = title.strip()
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

