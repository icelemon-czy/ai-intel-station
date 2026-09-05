from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


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
    discovered_at: str | None = None
    signal_role: str | None = None
    discovery_method: str | None = None
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
        self.discovered_at = _clean_text(self.discovered_at)
        self.signal_role = _clean_text(self.signal_role)
        if self.signal_role not in (None, "signal", "evidence"):
            raise ValueError(
                f"signal_role must be 'signal', 'evidence', or None; got {self.signal_role!r}"
            )
        self.discovery_method = _clean_text(self.discovery_method)
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


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _normalize_output_path(path: str | Path | None) -> str | None:
    """Normalize ``path`` to a string relative to ``REPO_ROOT`` when possible.

    Four input shapes collapse to ``None``:
      - ``None`` (caller passed no path)
      - empty string (often used as a "no path" sentinel)
      - whitespace-only (after stripping becomes empty)
      - non-string / non-Path (e.g. a numeric sentinel that was
        accidentally passed instead of a path) — without this guard
        a non-path value slipped through ``str(path)`` and produced
        a literal ``"123"`` filename that downstream ``build_paper_item``
        used as the markdown_path.

    Collapsing whitespace-only paths to ``None`` is what makes the
    ``filter value not in (None, "", [], {})`` short-circuit in
    ``__post_init__`` consistent: a path that was set but never written
    is treated the same as no path at all.
    """
    if path is None:
        return None
    if not isinstance(path, (str, Path)):
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
        discovered_at=utc_now_iso(),
        signal_role="evidence",
        discovery_method="github-repository",
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
                published_at=repo.get("createdAt"),
                updated_at=repo.get("updatedAt"),
                discovered_at=utc_now_iso(),
                signal_role="evidence",
                discovery_method="github-repository-search",
                output_path=markdown_path,
                metadata={
                    "query": query,
                    "owner": owner or parsed_owner,
                    "repo": repo.get("name") or parsed_repo,
                    "stargazer_count": (
                        repo.get("stargazersCount")
                        if repo.get("stargazersCount") is not None
                        else repo.get("stargazerCount")
                    ),
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
        updated_at=paper.get("updated"),
        discovered_at=utc_now_iso(),
        signal_role="evidence",
        discovery_method="arxiv-category",
        tags=paper.get("categories") or [],
        output_path=markdown_path,
        metadata={
            "pdf_url": paper.get("pdf_url"),
            "arxiv_id": paper.get("arxiv_id"),
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
        discovered_at=utc_now_iso(),
        signal_role="signal",
        discovery_method=meta.get("discovery_method") or "direct-url",
        output_path=markdown_path,
        metadata={
            "publisher": author,
            "body_length": len(body_markdown or ""),
        },
    )


def build_hackernews_item(
    story: dict,
    markdown_path: Path,
    *,
    feed: str,
    discovered_at: str | None = None,
) -> ResearchItem:
    item_id = story.get("id")
    timestamp = story.get("time")
    published_at = None
    if isinstance(timestamp, (int, float)) and timestamp > 0:
        published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    score = story.get("score") if isinstance(story.get("score"), int) else 0
    comments = story.get("descendants") if isinstance(story.get("descendants"), int) else 0
    discussion_url = f"https://news.ycombinator.com/item?id={item_id}" if item_id is not None else None
    return ResearchItem(
        source="hackernews",
        item_type="story",
        title=story.get("title") or f"Hacker News item {item_id or ''}".strip(),
        canonical_url=story.get("url") or discussion_url,
        authors=[story["by"]] if story.get("by") else [],
        published_at=published_at,
        discovered_at=discovered_at or utc_now_iso(),
        signal_role="signal",
        discovery_method=f"hackernews-{feed}",
        output_path=markdown_path,
        metadata={
            "feed": feed,
            "item_id": item_id,
            "discussion_url": discussion_url,
            "score": score,
            "comment_count": comments,
            "engagement_count": score + comments,
        },
    )


def build_x_item(
    post: dict,
    markdown_path: Path,
    *,
    query: str,
    discovered_at: str | None = None,
) -> ResearchItem:
    post_id = str(post.get("id") or "").strip()
    metrics = post.get("public_metrics") if isinstance(post.get("public_metrics"), dict) else {}
    engagement_count = sum(
        int(metrics.get(key) or 0)
        for key in ("like_count", "retweet_count", "reply_count", "quote_count", "bookmark_count")
        if isinstance(metrics.get(key, 0), (int, float))
    )
    text = str(post.get("text") or "").strip()
    return ResearchItem(
        source="x",
        item_type="post",
        title=text[:140] or f"X post {post_id}",
        canonical_url=f"https://x.com/i/web/status/{post_id}" if post_id else None,
        summary=text,
        authors=[str(post["author_id"])] if post.get("author_id") else [],
        published_at=post.get("created_at"),
        discovered_at=discovered_at or utc_now_iso(),
        signal_role="signal",
        discovery_method="x-recent-search",
        output_path=markdown_path,
        metadata={
            "query": query,
            "post_id": post_id,
            "public_metrics": metrics,
            "engagement_count": engagement_count,
        },
    )


def hackernews_story_markdown(item: ResearchItem) -> str:
    """Render one Hacker News story's local material.

    Shared by ``collect.hackernews`` (fresh collection) and the archive
    migration (materializing historical feed items) so the two never drift.
    """
    meta = item.metadata
    lines = [
        f"# {item.title}",
        "",
        f"- Source: Hacker News ({meta.get('feed', 'unknown')})",
        f"- Original: {item.canonical_url or 'n/a'}",
        f"- Discussion: {meta.get('discussion_url') or 'n/a'}",
        f"- Published: {item.published_at or 'unknown'}",
        f"- Score: {meta.get('score', 0)} · Comments: {meta.get('comment_count', 0)}",
    ]
    if meta.get("feeds"):
        lines.append(f"- Feeds: {', '.join(meta['feeds'])}")
    return "\n".join(lines) + "\n"


def x_post_markdown(item: ResearchItem) -> str:
    """Render one X post's local material (shared by collector and migration)."""
    meta = item.metadata
    lines = [
        f"# {item.title}",
        "",
        f"- Source: X ({meta.get('query', 'unknown')})",
        f"- Permalink: {item.canonical_url or 'n/a'}",
        f"- Published: {item.published_at or 'unknown'}",
        f"- Engagement: {meta.get('engagement_count', 0)}",
        "",
        item.summary or "",
    ]
    return "\n".join(lines) + "\n"


def build_wechat_index_item(
    article: dict,
    markdown_path: Path,
    *,
    account: str,
    wechat_id: str,
    discovered_at: str | None = None,
) -> ResearchItem:
    return ResearchItem(
        source="wechat",
        item_type="article-index",
        title=article.get("title") or "Untitled WeChat article",
        canonical_url=article.get("url"),
        summary=article.get("summary"),
        authors=[account],
        published_at=article.get("published_at"),
        discovered_at=discovered_at or utc_now_iso(),
        signal_role="signal",
        discovery_method="wechat-public-index",
        output_path=markdown_path,
        metadata={
            "account": account,
            "wechat_id": wechat_id,
            "watchlist": True,
            "index_provider": article.get("index_provider") or "sogou",
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
    if output_path.is_file() and item.discovered_at:
        try:
            existing = json.loads(output_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            existing = None
        if isinstance(existing, dict) and existing.get("discovered_at"):
            item.discovered_at = str(existing["discovered_at"])
    _atomic_write_text(output_path, item.to_json())
    return output_path

def write_research_items_jsonl(items: list[ResearchItem], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    first_seen: dict[tuple[str, str], str] = {}
    existing_payloads: list[dict] = []
    if output_path.is_file():
        try:
            for raw in output_path.read_text(encoding="utf-8-sig").splitlines():
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    continue
                existing_payloads.append(payload)
                if not payload.get("discovered_at"):
                    continue
                key = (
                    str(payload.get("source") or ""),
                    str(payload.get("canonical_url") or payload.get("title") or ""),
                )
                first_seen[key] = str(payload["discovered_at"])
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            first_seen = {}
            existing_payloads = []
    current_keys: set[tuple[str, str]] = set()
    for item in items:
        key = (item.source, str(item.canonical_url or item.title))
        current_keys.add(key)
        if key in first_seen:
            item.discovered_at = first_seen[key]
    serialized = [item.to_dict() for item in items]
    # Keep older observations that are absent from the latest bounded feed.
    # Otherwise an item falling out of a Top-N snapshot for one run and
    # reappearing later would lose its true first-discovered timestamp.
    for payload in existing_payloads:
        key = (
            str(payload.get("source") or ""),
            str(payload.get("canonical_url") or payload.get("title") or ""),
        )
        if key not in current_keys:
            serialized.append(payload)
    body = "\n".join(json.dumps(payload, ensure_ascii=False) for payload in serialized)
    if body:
        body += "\n"
    _atomic_write_text(output_path, body)
    return output_path
