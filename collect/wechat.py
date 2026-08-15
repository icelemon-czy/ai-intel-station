from __future__ import annotations

import argparse
import asyncio
import html as html_mod
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

from library.items import build_wechat_item, write_research_item


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = ROOT_DIR / "output" / "wechat"
IMAGE_CONCURRENCY = 5
WECHAT_EXTRA_INSTALL_COMMAND = "uv sync --extra wechat"


class WeChatRuntimeDependencyError(RuntimeError):
    """Raised when the optional WeChat collection stack is not installed."""


def _load_wechat_runtime():
    try:
        import httpx  # noqa: F401
        import markdownify  # noqa: F401
        from bs4 import BeautifulSoup
        from camoufox.async_api import AsyncCamoufox
    except ImportError as exc:
        missing = getattr(exc, "name", None) or str(exc)
        raise WeChatRuntimeDependencyError(
            "WeChat collection uses an optional browser runtime "
            f"({missing} is unavailable). Install it with "
            f"`{WECHAT_EXTRA_INSTALL_COMMAND}` and retry."
        ) from exc
    return BeautifulSoup, AsyncCamoufox


def normalize_wechat_url(raw: str) -> str:
    s = str(raw or "").strip()
    if not s:
        return s

    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    if s.startswith("<") and s.endswith(">"):
        s = s[1:-1].strip()

    s = re.sub(r"\\+([:/&?=#%])", r"\1", s)
    s = html_mod.unescape(s)

    if s.startswith("mp.weixin.qq.com/") or s.startswith("//mp.weixin.qq.com/"):
        s = "https://" + s.lstrip("/")

    parsed = urlparse(s)
    if parsed.scheme in ("http", "https") and (parsed.hostname or "").lower() == "mp.weixin.qq.com":
        s = urlunparse(("https", "mp.weixin.qq.com", parsed.path, parsed.params, parsed.query, parsed.fragment))

    return s


def extract_publish_time(html: str) -> str:
    match = re.search(r"create_time\s*:\s*JsDecode\('([^']+)'\)", html)
    if match:
        value = match.group(1)
        try:
            timestamp = int(value)
            if timestamp > 0:
                return format_timestamp(timestamp)
        except ValueError:
            return value

    match = re.search(r"create_time\s*:\s*'(\d+)'", html)
    if match:
        try:
            return format_timestamp(int(match.group(1)))
        except (ValueError, OSError, OverflowError):
            return match.group(1)

    match = re.search(r'create_time\s*[:=]\s*["\']?(\d+)["\']?', html)
    if match:
        try:
            return format_timestamp(int(match.group(1)))
        except (ValueError, OSError, OverflowError):
            return match.group(1)

    return ""


def _safe_format_timestamp(ts: int) -> str:
    """Format ``ts`` as ``YYYY-MM-DD HH:MM:SS`` in UTC+8, with safe
    fallbacks for out-of-range and pre-epoch timestamps.

    The previous code only raised for strictly out-of-range values.
    A negative timestamp falls through and produces a 1970
    date with the timezone offset baked in — silently
    misrepresenting the post as a 1970-01-01 entry. The fix
    treats any timestamp <= 0 (or otherwise unparseable) as
    invalid and falls back to repr(ts).
    """
    from datetime import datetime, timedelta, timezone

    if ts <= 0:
        return repr(ts)
    tz = timezone(timedelta(hours=8))
    try:
        dt = datetime.fromtimestamp(ts, tz=tz)
    except (ValueError, OSError, OverflowError):
        return repr(ts)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_timestamp(ts: int) -> str:
    return _safe_format_timestamp(ts)


async def download_image(client, img_url: str, img_dir: Path, index: int, semaphore: asyncio.Semaphore) -> tuple[str, str | None]:
    async with semaphore:
        try:
            url = img_url if not img_url.startswith("//") else f"https:{img_url}"
            ext_match = re.search(r"wx_fmt=(\w+)", url) or re.search(r"\.(\w{3,4})(?:\?|$)", url)
            ext = ext_match.group(1) if ext_match else "png"

            filename = f"img_{index:03d}.{ext}"
            filepath = img_dir / filename

            response = await client.get(url, headers={"Referer": "https://mp.weixin.qq.com/"}, timeout=15.0)
            response.raise_for_status()
            # Cap to ~10 MB so a hostile server can't push gigabytes through us.
            # httpx has no built-in body-size limit; check Content-Length and
            # the actual content length before writing.
            content_length = response.headers.get("Content-Length")
            max_bytes = 10 * 1024 * 1024
            if content_length is not None:
                try:
                    if int(content_length) > max_bytes:
                        print(f"  ⚠ image {filename} too large ({content_length} bytes); skipping")
                        return img_url, None
                except ValueError:
                    pass
            if len(response.content) > max_bytes:
                print(f"  ⚠ image {filename} body too large; skipping")
                return img_url, None
            # Atomic write so a process crash mid-download cannot leave a
            # half-truncated image on disk that the user thinks is valid.
            tmp_path = filepath.with_suffix(filepath.suffix + ".tmp")
            tmp_path.write_bytes(response.content)
            os.replace(tmp_path, filepath)
            return img_url, f"images/{filename}"
        except Exception as exc:
            print(f"  ⚠ 图片下载失败: {exc}")
            return img_url, None


async def download_all_images(img_urls: list[str], img_dir: Path) -> dict[str, str]:
    if not img_urls:
        return {}

    import httpx

    print(f"🖼  下载 {len(img_urls)} 张图片 (并发 {IMAGE_CONCURRENCY})...")
    semaphore = asyncio.Semaphore(IMAGE_CONCURRENCY)
    async with httpx.AsyncClient() as client:
        tasks = [download_image(client, url, img_dir, index + 1, semaphore) for index, url in enumerate(img_urls)]
        results = await asyncio.gather(*tasks)

    url_map = {remote_url: local_path for remote_url, local_path in results if local_path}
    print(f"  ✅ {len(url_map)}/{len(img_urls)}")
    return url_map


def extract_metadata(soup, html: str) -> dict:
    title_el = soup.select_one("#activity-name")
    author_el = soup.select_one("#js_name")
    return {
        "title": title_el.get_text(strip=True) if title_el else "",
        "author": author_el.get_text(strip=True) if author_el else "",
        "publish_time": extract_publish_time(html),
    }


def process_content(soup) -> tuple[str, list[dict], list[str]]:
    content_el = soup.select_one("#js_content")
    if not content_el:
        return "", [], []

    for img in content_el.find_all("img"):
        data_src = img.get("data-src")
        if data_src:
            img["src"] = data_src

    code_blocks = []
    for el in content_el.select(".code-snippet__fix"):
        for line_idx in el.select(".code-snippet__line-index"):
            line_idx.decompose()

        pre = el.select_one("pre[data-lang]")
        lang = pre.get("data-lang", "") if pre else ""

        lines = []
        for code_tag in el.find_all("code"):
            text = code_tag.get_text()
            if re.match(r"^[ce]?ounter\(line", text):
                continue
            lines.append(text)

        if not lines:
            lines.append(el.get_text())

        placeholder = f"CODEBLOCK-PLACEHOLDER-{len(code_blocks)}"
        code_blocks.append({"lang": lang, "code": "\n".join(lines)})
        el.replace_with(soup.new_tag("p", string=placeholder))

    for selector in ("script", "style", ".qr_code_pc", ".reward_area"):
        for tag in content_el.select(selector):
            tag.decompose()

    img_urls = []
    seen = set()
    for img in content_el.find_all("img", src=True):
        src = img["src"]
        if src not in seen:
            seen.add(src)
            img_urls.append(src)

    return str(content_el), code_blocks, img_urls


def convert_to_markdown(content_html: str, code_blocks: list[dict]) -> str:
    import markdownify

    md = markdownify.markdownify(
        content_html,
        heading_style="ATX",
        bullets="-",
        convert=[
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "strong",
            "em",
            "a",
            "img",
            "ul",
            "ol",
            "li",
            "blockquote",
            "br",
            "hr",
            "table",
            "thead",
            "tbody",
            "tr",
            "th",
            "td",
            "pre",
            "code",
        ],
    )

    for index, block in enumerate(code_blocks):
        placeholder = f"CODEBLOCK-PLACEHOLDER-{index}"
        fenced = f"\n```{block['lang']}\n{block['code']}\n```\n"
        md = md.replace(placeholder, fenced)

    md = md.replace("\u00a0", " ")
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    md = re.sub(r"[ \t]+$", "", md, flags=re.MULTILINE)
    return md


def replace_image_urls(md: str, url_map: dict[str, str]) -> str:
    for remote_url, local_path in url_map.items():
        pattern = re.compile(r"!\[([^\]]*)\]\(" + re.escape(remote_url) + r"\)")
        md = pattern.sub(lambda match: f"![{match.group(1)}]({local_path})", md)
    return md


def build_markdown(meta: dict, body_md: str) -> str:
    # Replace newlines in the title with a space so the H1 heading
    # stays a single line — 'foo\nbar' would otherwise render as a
    # single H1 across two visual lines that some markdown renderers
    # split into two H1s.
    title = (meta.get("title") or "").replace("\n", " ").replace("\r", " ").strip() or "Untitled"
    lines = [f"# {title}", ""]
    if meta.get("author"):
        lines.append(f"> 公众号: {meta['author']}")
    if meta.get("publish_time"):
        lines.append(f"> 发布时间: {meta['publish_time']}")
    if meta.get("source_url"):
        lines.append(f"> 原文链接: {meta['source_url']}")
    if meta.get("author") or meta.get("publish_time") or meta.get("source_url"):
        lines.append("")
    lines.extend(["---", ""])
    return "\n".join(lines) + body_md


async def fetch_article(url: str, output_dir: Path | None = None) -> Path:
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    BeautifulSoup, AsyncCamoufox = _load_wechat_runtime()

    print(f"🔄 正在抓取: {url}")
    print("🦊 启动 Camoufox 浏览器...")
    async with AsyncCamoufox(headless=True) as browser:
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded")
        try:
            await page.wait_for_selector("#js_content", timeout=10000)
        except Exception:
            pass
        await asyncio.sleep(2)
        html = await page.content()

    soup = BeautifulSoup(html, "html.parser")
    meta = extract_metadata(soup, html)
    if not meta["title"]:
        print("❌ 未能提取到文章标题，可能触发了验证码")
        output_dir.mkdir(parents=True, exist_ok=True)
        debug_path = output_dir / "debug.html"
        debug_path.write_text(html, encoding="utf-8")
        print(f"已保存原始 HTML 到 {debug_path}")
        raise RuntimeError("WeChat article title was unavailable; verification may be required")

    meta["source_url"] = url
    print(f"📄 标题: {meta.get('title', '')}")
    print(f"👤 作者: {meta.get('author', '')}")
    print(f"📅 时间: {meta.get('publish_time', '')}")

    content_html, code_blocks, img_urls = process_content(soup)
    if not content_html:
        print("❌ 未能提取到正文内容")
        raise RuntimeError("WeChat article body was unavailable")

    md = convert_to_markdown(content_html, code_blocks)

    raw_safe = re.sub(r'[/\\?%*:|"<>]', "_", meta["title"])[:80]
    safe_title = raw_safe.strip("_") or "untitled"
    article_dir = output_dir / safe_title
    img_dir = article_dir / "images"
    # If the article directory already exists, suffix a counter so a
    # follow-up collect with the same title does not silently overwrite
    # the previous archive copy.
    counter = 1
    while article_dir.exists():
        article_dir = output_dir / f"{safe_title}-{counter}"
        img_dir = article_dir / "images"
        counter += 1
    img_dir.mkdir(parents=True, exist_ok=True)

    url_map = await download_all_images(img_urls, img_dir)
    md = replace_image_urls(md, url_map)

    result = build_markdown(meta, md)
    md_path = article_dir / f"{safe_title}.md"
    md_path.write_text(result, encoding="utf-8")
    write_research_item(build_wechat_item(meta, md_path, body_markdown=md), article_dir / "research-item.json")

    print(f"✅ 已保存: {md_path}")
    print(f"📊 Markdown 约 {len(md)} 字符")
    return md_path


def main() -> None:
    parser = argparse.ArgumentParser(description="微信公众号文章抓取 & Markdown 转换工具")
    parser.add_argument("url", help="微信公众号文章 URL")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    args = parser.parse_args()

    raw_url = args.url
    url = normalize_wechat_url(raw_url)
    if url != raw_url:
        print("ℹ️  已自动清理 URL 中的转义字符 / HTML 实体。")

    if not url.startswith("https://mp.weixin.qq.com/"):
        print("❌ 请输入有效的微信文章 URL (mp.weixin.qq.com)")
        print("提示：请用引号包住完整 URL；若粘贴后出现反斜杠转义，脚本会自动清理。")
        sys.exit(1)

    try:
        asyncio.run(fetch_article(url, output_dir=args.output))
    except Exception as exc:
        print(f"❌ 抓取失败: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
