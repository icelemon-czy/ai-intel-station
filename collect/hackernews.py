from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from library.items import build_hackernews_item, write_research_items_jsonl


API_ROOT = "https://hacker-news.firebaseio.com/v0"
SUPPORTED_FEEDS = ("topstories", "newstories", "beststories", "askstories", "showstories")
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
MAX_SCANNED_ITEMS = 100


class HackerNewsFetchError(RuntimeError):
    pass


def request_json(url: str, *, timeout: float = 20.0, max_bytes: int = MAX_RESPONSE_BYTES):
    request = Request(url, headers={"User-Agent": "ai-intel-station/0.2"})
    try:
        with urlopen(request, timeout=timeout) as response:
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > max_bytes:
                        raise HackerNewsFetchError(f"response exceeds {max_bytes}-byte limit: {url}")
                except ValueError:
                    pass
            raw = response.read(max_bytes + 1)
    except HackerNewsFetchError:
        raise
    except Exception as exc:
        raise HackerNewsFetchError(f"request failed for {url}: {exc}") from exc
    if len(raw) > max_bytes:
        raise HackerNewsFetchError(f"response exceeds {max_bytes}-byte limit: {url}")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HackerNewsFetchError(f"malformed JSON from {url}: {exc}") from exc


def _matches_keywords(story: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True
    haystack = " ".join(
        str(story.get(key) or "") for key in ("title", "text", "url")
    ).lower()
    return any(keyword.lower() in haystack for keyword in keywords)


def collect_feed(
    feed: str,
    *,
    keywords: list[str],
    limit: int,
    output_dir: Path,
    request_json: Callable[..., object] = request_json,
    discovered_at: str | None = None,
) -> Path:
    if feed not in SUPPORTED_FEEDS:
        raise HackerNewsFetchError(f"unsupported Hacker News feed: {feed}")
    if limit <= 0 or limit > MAX_SCANNED_ITEMS:
        raise HackerNewsFetchError(f"limit must be between 1 and {MAX_SCANNED_ITEMS}")

    feed_url = f"{API_ROOT}/{feed}.json"
    try:
        ids = request_json(feed_url)
    except Exception as exc:
        if isinstance(exc, HackerNewsFetchError):
            raise
        raise HackerNewsFetchError(f"{feed} request failed: {exc}") from exc
    if not isinstance(ids, list) or any(not isinstance(item_id, int) for item_id in ids):
        raise HackerNewsFetchError(f"{feed} returned malformed item id list")

    feed_dir = Path(output_dir) / feed
    feed_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = feed_dir / "signals.md"
    items = []
    for item_id in ids[:MAX_SCANNED_ITEMS]:
        if len(items) >= limit:
            break
        item_url = f"{API_ROOT}/item/{item_id}.json"
        try:
            story = request_json(item_url)
        except Exception as exc:
            if isinstance(exc, HackerNewsFetchError):
                raise
            raise HackerNewsFetchError(f"{feed} item {item_id} request failed: {exc}") from exc
        if not isinstance(story, dict):
            raise HackerNewsFetchError(f"{feed} item {item_id} returned malformed payload")
        if story.get("deleted") or story.get("dead") or story.get("type") != "story":
            continue
        if not _matches_keywords(story, keywords):
            continue
        items.append(
            build_hackernews_item(
                story,
                markdown_path,
                feed=feed,
                discovered_at=discovered_at,
            )
        )

    lines = [f"# Hacker News: {feed}", "", f"Matched {len(items)} signal(s)", ""]
    for item in items:
        lines.extend(
            [
                f"## [{item.title}]({item.canonical_url})",
                f"- Published: {item.published_at or 'unknown'}",
                f"- Discussion: {item.metadata.get('discussion_url', '')}",
                f"- Score: {item.metadata.get('score', 0)}",
                f"- Comments: {item.metadata.get('comment_count', 0)}",
                "",
            ]
        )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    write_research_items_jsonl(items, feed_dir / "research-items.jsonl")
    return markdown_path
