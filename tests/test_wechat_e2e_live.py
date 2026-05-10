from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

import collect.wechat as wechat_collect


pytestmark = pytest.mark.e2e


def _get_e2e_urls() -> list[str]:
    raw = os.getenv("WECHAT_E2E_URLS", "").strip()
    if not raw:
        return []
    return [url.strip() for url in raw.split(",") if url.strip()]


def _contains_url(md_files: list[Path], url: str) -> bool:
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        if url in text:
            return True
    return False


def test_live_articles_end_to_end(tmp_path: Path) -> None:
    urls = _get_e2e_urls()
    if not urls:
        pytest.skip("Set WECHAT_E2E_URLS to run live e2e test")

    timeout = int(os.getenv("WECHAT_E2E_TIMEOUT", "240"))
    out_dir = tmp_path / "output"

    for url in urls:
        asyncio.run(asyncio.wait_for(wechat_collect.fetch_article(url, output_dir=out_dir / "wechat"), timeout=timeout))

    md_files = list(out_dir.rglob("*.md"))
    assert md_files, "Expected at least one markdown file from e2e fetch"

    for url in urls:
        assert _contains_url(md_files, url), f"Expected markdown to include source URL: {url}"
