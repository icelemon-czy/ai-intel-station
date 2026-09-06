from __future__ import annotations

import json
from pathlib import Path
from typing import Callable
from urllib.request import Request, urlopen

from ai_intel_station.library.archive_paths import hackernews_leaf
from ai_intel_station.library.items import build_hackernews_item, hackernews_story_markdown, write_research_item


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

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stories: list[Path] = []
    rank = 0
    for item_id in ids[:MAX_SCANNED_ITEMS]:
        if len(stories) >= limit:
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
        rank += 1
        # One primary unit per stable story id: feed / rank / discovered date are
        # provenance inside the sidecar, and a story seen in several feeds never
        # duplicates its material.
        markdown_path = output_dir / hackernews_leaf(story.get("id"))
        item = build_hackernews_item(story, markdown_path, feed=feed, discovered_at=discovered_at)
        item.metadata["rank"] = rank
        _accumulate_feed_provenance(item, output_dir / hackernews_leaf(story.get("id"), suffix=".research-item.json"))
        markdown_path.write_text(hackernews_story_markdown(item), encoding="utf-8")
        write_research_item(item, output_dir / hackernews_leaf(item_id, suffix=".research-item.json"))
        stories.append(markdown_path)

    print(f"✅ Saved {len(stories)} Hacker News {feed} story unit(s) to {output_dir}")
    return stories[0] if stories else output_dir


def _accumulate_feed_provenance(item, sidecar_path: Path) -> None:
    """Keep the set of feeds a story was discovered through across collections."""
    try:
        existing = json.loads(sidecar_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeDecodeError):
        existing = None
    feeds: list[str] = []
    if isinstance(existing, dict):
        prior = (existing.get("metadata") or {}).get("feeds")
        if isinstance(prior, list):
            feeds.extend(str(f) for f in prior)
    current = item.metadata.get("feed")
    if current and current not in feeds:
        feeds.append(str(current))
    if feeds:
        item.metadata["feeds"] = feeds


def collect_topic(
    topic: str,
    *,
    feeds: list[str],
    limit: int,
    output_dir: Path,
    known_urls: set[str] | None = None,
    request_json: Callable[..., object] = request_json,
    discovered_at: str | None = None,
) -> tuple[list, list]:
    """Scan ``feeds`` in order for stories whose title/url match ``topic``.

    Interest Sweep uses this instead of Algolia: it reuses the existing Firebase
    feed + ``_matches_keywords`` filter already in ``collect_feed``. Matches are
    unique by story id and capped at ``limit`` total matches across the feeds.
    Returns ``(new_items, existing_items)`` — a story whose ``canonical_url`` (the
    same URL ``build_hackernews_item`` assigns) is already in ``known_urls`` is a
    Library hit: reported but not re-persisted. Only new stories write the
    Markdown + sidecar unit, using the same per-story identity ``collect_feed``
    uses. ``request_json`` is injectable so a sweep can be tested offline.
    """
    known_urls = known_urls or set()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seen_ids: set = set()
    matched = 0
    new_items: list = []
    existing_items: list = []

    for feed in feeds:
        if feed not in SUPPORTED_FEEDS:
            raise HackerNewsFetchError(f"unsupported Hacker News feed: {feed}")
        if matched >= limit:
            break
        try:
            ids = request_json(f"{API_ROOT}/{feed}.json")
        except Exception as exc:
            if isinstance(exc, HackerNewsFetchError):
                raise
            raise HackerNewsFetchError(f"{feed} request failed: {exc}") from exc
        if not isinstance(ids, list) or any(not isinstance(item_id, int) for item_id in ids):
            raise HackerNewsFetchError(f"{feed} returned malformed item id list")

        for item_id in ids[:MAX_SCANNED_ITEMS]:
            if matched >= limit:
                break
            if item_id in seen_ids:
                continue
            try:
                story = request_json(f"{API_ROOT}/item/{item_id}.json")
            except Exception as exc:
                if isinstance(exc, HackerNewsFetchError):
                    raise
                raise HackerNewsFetchError(f"{feed} item {item_id} request failed: {exc}") from exc
            if not isinstance(story, dict):
                raise HackerNewsFetchError(f"{feed} item {item_id} returned malformed payload")
            if story.get("deleted") or story.get("dead") or story.get("type") != "story":
                continue
            if not _matches_keywords(story, [topic]):
                continue

            seen_ids.add(item_id)
            matched += 1
            markdown_path = output_dir / hackernews_leaf(item_id)
            item = build_hackernews_item(story, markdown_path, feed=feed, discovered_at=discovered_at)
            if item.canonical_url and item.canonical_url in known_urls:
                existing_items.append(item)
                continue
            _accumulate_feed_provenance(
                item, output_dir / hackernews_leaf(item_id, suffix=".research-item.json")
            )
            markdown_path.write_text(hackernews_story_markdown(item), encoding="utf-8")
            write_research_item(item, output_dir / hackernews_leaf(item_id, suffix=".research-item.json"))
            new_items.append(item)

    return new_items, existing_items
