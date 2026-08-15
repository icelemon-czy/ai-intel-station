from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from library.items import build_x_item, write_research_items_jsonl


RECENT_SEARCH_URL = "https://api.x.com/2/tweets/search/recent"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class XCredentialError(RuntimeError):
    pass


class XFetchError(RuntimeError):
    pass


def request_json(
    url: str,
    *,
    bearer_token: str,
    timeout: float = 20.0,
    max_bytes: int = MAX_RESPONSE_BYTES,
):
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {bearer_token}",
            "User-Agent": "ai-intel-station/0.2",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
    except Exception as exc:
        raise XFetchError(f"X recent search failed: {exc}") from exc
    if len(raw) > max_bytes:
        raise XFetchError(f"X response exceeds {max_bytes}-byte limit")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise XFetchError(f"X returned malformed JSON: {exc}") from exc


def collect_recent_search(
    query: str,
    *,
    token_env: str,
    limit: int,
    output_dir: Path,
    request_json: Callable[..., object] = request_json,
    discovered_at: str | None = None,
    freshness_hours: int = 48,
    now: datetime | None = None,
) -> Path:
    token = os.environ.get(token_env, "").strip()
    if not token:
        raise XCredentialError(
            f"X source requires bearer token in environment variable {token_env}"
        )
    if limit < 10 or limit > 100:
        raise XFetchError("X recent-search limit must be between 10 and 100")
    if freshness_hours <= 0 or freshness_hours > 72:
        raise XFetchError("X recent-search freshness_hours must be between 1 and 72")
    evaluation_time = now or datetime.now(timezone.utc)
    if evaluation_time.tzinfo is None:
        evaluation_time = evaluation_time.replace(tzinfo=timezone.utc)
    evaluation_time = evaluation_time.astimezone(timezone.utc).replace(microsecond=0)
    start_time = evaluation_time - timedelta(hours=freshness_hours)

    def _rfc3339(value: datetime) -> str:
        return value.isoformat().replace("+00:00", "Z")

    params = urlencode(
        {
            "query": query,
            "max_results": limit,
            "start_time": _rfc3339(start_time),
            "end_time": _rfc3339(evaluation_time),
            "tweet.fields": "created_at,author_id,public_metrics,lang,entities",
        }
    )
    url = f"{RECENT_SEARCH_URL}?{params}"
    try:
        payload = request_json(url, bearer_token=token)
    except Exception as exc:
        if isinstance(exc, (XCredentialError, XFetchError)):
            raise
        raise XFetchError(f"X recent search failed for {query!r}: {exc}") from exc
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("data", []), list)
        or (payload.get("errors") and "data" not in payload)
    ):
        raise XFetchError(f"X recent search returned malformed payload for {query!r}")

    safe_query = re.sub(r"[^\w\-一-鿿]+", "-", query.lower()).strip("-")[:80] or "query"
    query_dir = Path(output_dir) / safe_query
    query_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = query_dir / "signals.md"
    items = [
        build_x_item(
            post,
            markdown_path,
            query=query,
            discovered_at=discovered_at,
        )
        for post in payload.get("data", [])
        if isinstance(post, dict) and post.get("id") and post.get("created_at")
    ]
    lines = [f"# X recent search: {query}", "", f"Found {len(items)} signal(s)", ""]
    for item in items:
        lines.extend(
            [
                f"## [{item.title}]({item.canonical_url})",
                f"- Published: {item.published_at}",
                f"- Engagement: {item.metadata.get('engagement_count', 0)}",
                "",
            ]
        )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    write_research_items_jsonl(items, query_dir / "research-items.jsonl")
    return markdown_path
