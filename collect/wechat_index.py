from __future__ import annotations

import html as html_module
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import quote
from urllib.request import Request, urlopen

from library.items import build_wechat_index_item, write_research_items_jsonl


SEARCH_URL = "https://weixin.sogou.com/weixin?type=2&query={query}"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
BLOCK_MARKERS = (
    "当前环境异常",
    "完成验证后即可继续访问",
    "请输入验证码",
    "访问过于频繁",
    "antispider",
)


class WeChatIndexCoverageError(RuntimeError):
    pass


def request_text(url: str, *, timeout: float = 20.0, max_bytes: int = MAX_RESPONSE_BYTES) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 Chrome/124 Safari/537.36"
            )
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read(max_bytes + 1)
    except Exception as exc:
        raise WeChatIndexCoverageError(f"public index request failed: {exc}") from exc
    if len(raw) > max_bytes:
        raise WeChatIndexCoverageError(
            f"public index response exceeds {max_bytes}-byte limit"
        )
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise WeChatIndexCoverageError(f"public index returned invalid UTF-8: {exc}") from exc


def _strip_tags(value: str) -> str:
    return " ".join(
        html_module.unescape(re.sub(r"<[^>]+>", " ", value)).split()
    )


def parse_index_html(body: str, *, account: str, limit: int) -> list[dict]:
    lowered = body.lower()
    if any(marker.lower() in lowered for marker in BLOCK_MARKERS):
        raise WeChatIndexCoverageError(
            "public index requires verification or reports abnormal access"
        )

    articles = []
    for block in re.findall(r"<li\b[^>]*>(.*?)</li>", body, flags=re.I | re.S):
        link = re.search(
            r"<h3\b[^>]*>.*?<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
            block,
            flags=re.I | re.S,
        )
        if not link:
            continue
        account_matches = re.findall(
            r"<(?:a|span)\b[^>]*class=[\"'][^\"']*(?:account|s2)[^\"']*[\"'][^>]*>(.*?)</(?:a|span)>",
            block,
            flags=re.I | re.S,
        )
        accounts = [_strip_tags(value) for value in account_matches]
        if not accounts or not any(account in value for value in accounts):
            continue
        timestamp_match = re.search(
            r"(?:all-time-y2[^>]*>|timeConvert\([\"']?)(\d{9,12})",
            block,
            flags=re.I | re.S,
        )
        if not timestamp_match:
            raise WeChatIndexCoverageError(
                f"public index result for {account} omitted publication time"
            )
        timestamp = int(timestamp_match.group(1))
        if timestamp <= 0:
            raise WeChatIndexCoverageError(
                f"public index result for {account} has invalid publication time"
            )
        summary_match = re.search(
            r"<p\b[^>]*class=[\"'][^\"']*txt-info[^\"']*[\"'][^>]*>(.*?)</p>",
            block,
            flags=re.I | re.S,
        )
        published_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace("+00:00", "Z")
        url = html_module.unescape(link.group(1)).strip()
        if url.startswith("/"):
            url = f"https://weixin.sogou.com{url}"
        articles.append(
            {
                "title": _strip_tags(link.group(2)),
                "url": url,
                "summary": _strip_tags(summary_match.group(1)) if summary_match else None,
                "published_at": published_at,
                "index_provider": "sogou",
            }
        )
        if len(articles) >= limit:
            break
    if not articles:
        raise WeChatIndexCoverageError(
            f"public index returned no attributable parseable result for {account}"
        )
    return articles


def collect_account(
    account: str,
    wechat_id: str,
    *,
    limit: int,
    output_dir: Path,
    request_text: Callable[..., str] = request_text,
    discovered_at: str | None = None,
) -> Path:
    query = quote(f'"{account}（{wechat_id}）"')
    url = SEARCH_URL.format(query=query)
    try:
        body = request_text(url)
    except Exception as exc:
        if isinstance(exc, WeChatIndexCoverageError):
            raise
        raise WeChatIndexCoverageError(
            f"public index request failed for {account}: {exc}"
        ) from exc
    articles = parse_index_html(body, account=account, limit=limit)

    safe_account = re.sub(r"[^\w\-\u4e00-\u9fff]+", "-", account).strip("-") or "account"
    account_dir = Path(output_dir) / f"watch-{safe_account}"
    account_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = account_dir / "signals.md"
    items = [
        build_wechat_index_item(
            article,
            markdown_path,
            account=account,
            wechat_id=wechat_id,
            discovered_at=discovered_at,
        )
        for article in articles
    ]
    lines = [f"# WeChat watchlist: {account}", "", f"Found {len(items)} signal(s)", ""]
    for item in items:
        lines.extend(
            [
                f"## [{item.title}]({item.canonical_url})",
                f"- Account: {account} ({wechat_id})",
                f"- Published: {item.published_at}",
                f"- {item.summary or ''}",
                "",
            ]
        )
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    write_research_items_jsonl(items, account_dir / "research-items.jsonl")
    return markdown_path
