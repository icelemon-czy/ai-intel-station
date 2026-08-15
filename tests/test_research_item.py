from __future__ import annotations

import asyncio
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pytest

from library.items import (
    backfill_output_tree,
    build_github_repo_item,
    build_wechat_item,
    parse_github_repo_markdown,
    parse_github_search_markdown,
    parse_paper_markdown,
    parse_wechat_markdown,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB_REPO_SAMPLE = REPO_ROOT / "output" / "github" / "anthropics-claude-code" / "README.md"
GITHUB_SEARCH_SAMPLE = REPO_ROOT / "output" / "github" / "claude-code-agent" / "search.md"
PAPER_SAMPLE = REPO_ROOT / "output" / "papers" / "arXiv-cs.AI" / "01-Personalized Worked Example Generation from Studen.md"
WECHAT_SAMPLE = (
    REPO_ROOT
    / "output"
    / "wechat"
    / "Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远"
    / "Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远.md"
)


def test_build_github_repo_item_normalizes_repository_metadata() -> None:
    item = build_github_repo_item(
        owner="anthropic",
        repo="claude-code",
        data={
            "name": "claude-code",
            "description": "Agentic coding tool",
            "url": "https://github.com/anthropic/claude-code",
            "stargazerCount": 10,
            "primaryLanguage": {"name": "Shell"},
            "repositoryTopics": [{"topic": {"name": "agent"}}, {"topic": {"name": "cli"}}],
            "createdAt": "2025-02-22T00:00:00Z",
            "updatedAt": "2026-04-22T00:00:00Z",
            "issues": [],
        },
        markdown_path=Path("output/github/anthropic-claude-code/README.md"),
    )

    assert item.source == "github"
    assert item.item_type == "repository"
    assert item.title == "claude-code"
    assert item.canonical_url == "https://github.com/anthropic/claude-code"
    assert item.summary == "Agentic coding tool"
    assert item.published_at == "2025-02-22T00:00:00Z"
    assert item.updated_at == "2026-04-22T00:00:00Z"
    assert item.discovered_at is not None
    assert item.signal_role == "evidence"
    assert item.discovery_method == "github-repository"
    assert item.tags == ["agent", "cli"]
    assert item.metadata["owner"] == "anthropic"
    assert item.metadata["repo"] == "claude-code"
    assert item.metadata["stargazer_count"] == 10
    assert item.metadata["primary_language"] == "Shell"
    assert item.metadata["issue_count"] == 0
    assert item.output_path == "output/github/anthropic-claude-code/README.md"


def test_build_wechat_item_allows_missing_optional_fields() -> None:
    item = build_wechat_item(
        meta={
            "title": "Harness",
            "author": "",
            "publish_time": "",
            "source_url": "https://mp.weixin.qq.com/s/example",
        },
        markdown_path=Path("output/wechat/Harness/Harness.md"),
    )

    assert item.source == "wechat"
    assert item.item_type == "article"
    assert item.title == "Harness"
    assert item.canonical_url == "https://mp.weixin.qq.com/s/example"
    assert item.authors == []
    assert item.published_at is None
    assert item.discovered_at is not None
    assert item.signal_role == "signal"
    assert item.discovery_method == "direct-url"
    assert item.tags == []
    payload = json.loads(item.to_json())
    assert payload["authors"] == []
    assert payload["published_at"] is None
    assert payload["tags"] == []


def test_parse_existing_output_samples_into_research_items() -> None:
    repo_item = parse_github_repo_markdown(GITHUB_REPO_SAMPLE)
    search_items = parse_github_search_markdown(GITHUB_SEARCH_SAMPLE)
    paper_item = parse_paper_markdown(PAPER_SAMPLE)
    wechat_item = parse_wechat_markdown(WECHAT_SAMPLE)

    assert repo_item.source == "github"
    assert repo_item.item_type == "repository"
    assert repo_item.canonical_url == "https://github.com/anthropics/claude-code"

    assert len(search_items) == 10
    assert search_items[0].source == "github"
    assert search_items[0].item_type == "search-result"
    assert search_items[0].canonical_url.startswith("https://github.com/")

    assert paper_item.source == "papers"
    assert paper_item.item_type == "paper"
    assert paper_item.title == "Personalized Worked Example Generation from Student Code Submissions using Pattern-based Knowledge Components"
    assert paper_item.canonical_url == "https://arxiv.org/abs/2604.24758v1"
    assert paper_item.summary.startswith("Adaptive programming practice often relies on fixed libraries")
    assert paper_item.authors == ["Griffin Pitts", "Muntasir Hoq", "Peter Brusilovsky", "Narges Norouzi", "Arto Hellas"]
    assert paper_item.published_at == "2026-04-27"
    assert paper_item.tags == ["cs.HC", "cs.AI", "cs.CY"]
    assert paper_item.metadata["authors_total"] == 7

    assert wechat_item.source == "wechat"
    assert wechat_item.item_type == "article"
    assert wechat_item.title == "Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远"
    assert wechat_item.canonical_url == "https://mp.weixin.qq.com/s/h49UiGERvz8BMkMW0_4Gwg"
    assert wechat_item.authors == ["架构师"]
    assert wechat_item.published_at == "2026-04-19 22:26"
    assert wechat_item.summary.startswith("架构师（JiaGouX）")
    assert wechat_item.metadata["publisher"] == "架构师"


def test_backfill_output_tree_writes_expected_sidecars(tmp_path: Path) -> None:
    output_root = tmp_path / "output"

    repo_dir = output_root / "github" / "anthropics-claude-code"
    repo_dir.mkdir(parents=True)
    shutil.copy2(GITHUB_REPO_SAMPLE, repo_dir / "README.md")
    repo_markdown_before = repo_dir.joinpath("README.md").read_text(encoding="utf-8")

    search_dir = output_root / "github" / "claude-code-agent"
    search_dir.mkdir(parents=True)
    shutil.copy2(GITHUB_SEARCH_SAMPLE, search_dir / "search.md")
    search_markdown_before = search_dir.joinpath("search.md").read_text(encoding="utf-8")

    paper_dir = output_root / "papers" / "arXiv-cs.AI"
    paper_dir.mkdir(parents=True)
    paper_md = paper_dir / "01-sample.md"
    shutil.copy2(PAPER_SAMPLE, paper_md)
    paper_markdown_before = paper_md.read_text(encoding="utf-8")

    wechat_dir = output_root / "wechat" / "sample-article"
    wechat_dir.mkdir(parents=True)
    wechat_md = wechat_dir / "sample-article.md"
    shutil.copy2(WECHAT_SAMPLE, wechat_md)
    wechat_markdown_before = wechat_md.read_text(encoding="utf-8")

    written = backfill_output_tree(output_root)

    repo_sidecar = repo_dir / "research-item.json"
    search_sidecar = search_dir / "research-items.jsonl"
    paper_sidecar = paper_dir / "01-sample.research-item.json"
    wechat_sidecar = wechat_dir / "research-item.json"

    assert repo_sidecar in written
    assert search_sidecar in written
    assert paper_sidecar in written
    assert wechat_sidecar in written

    repo_payload = json.loads(repo_sidecar.read_text(encoding="utf-8"))
    assert repo_payload["source"] == "github"
    assert repo_payload["item_type"] == "repository"

    search_lines = [line for line in search_sidecar.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(search_lines) == 10
    assert json.loads(search_lines[0])["item_type"] == "search-result"

    paper_payload = json.loads(paper_sidecar.read_text(encoding="utf-8"))
    assert paper_payload["source"] == "papers"

    wechat_payload = json.loads(wechat_sidecar.read_text(encoding="utf-8"))
    assert wechat_payload["source"] == "wechat"

    assert repo_dir.joinpath("README.md").read_text(encoding="utf-8") == repo_markdown_before
    assert search_dir.joinpath("search.md").read_text(encoding="utf-8") == search_markdown_before
    assert paper_md.read_text(encoding="utf-8") == paper_markdown_before
    assert wechat_md.read_text(encoding="utf-8") == wechat_markdown_before


def test_save_repo_writes_markdown_and_research_item_sidecar(tmp_path: Path, monkeypatch) -> None:
    from collect import github

    def fake_fetch_repo(owner: str, repo: str) -> dict:
        assert (owner, repo) == ("anthropic", "claude-code")
        return {
            "name": "claude-code",
            "description": "Agentic coding tool",
            "url": "https://github.com/anthropic/claude-code",
            "stargazerCount": 10,
            "primaryLanguage": {"name": "Shell"},
            "repositoryTopics": [{"topic": {"name": "agent"}}],
            "createdAt": "2025-02-22T00:00:00Z",
            "updatedAt": "2026-04-22T00:00:00Z",
            "issues": [
                {
                    "number": 7,
                    "title": "Support local mode",
                    "labels": [{"name": "enhancement"}],
                    "author": {"login": "octo"},
                }
            ],
        }

    monkeypatch.setattr(github, "fetch_repo", fake_fetch_repo)

    github.save_repo("anthropic", "claude-code", tmp_path)

    repo_dir = tmp_path / "anthropic-claude-code"
    markdown_path = repo_dir / "README.md"
    sidecar_path = repo_dir / "research-item.json"

    assert markdown_path.exists()
    assert sidecar_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# claude-code" in markdown
    assert "- ⭐ Stars: 10" in markdown
    assert "- [#7] [enhancement] Support local mode (@octo)" in markdown

    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert payload["source"] == "github"
    assert payload["item_type"] == "repository"
    assert payload["canonical_url"] == "https://github.com/anthropic/claude-code"
    assert payload["published_at"] == "2025-02-22T00:00:00Z"
    assert payload["updated_at"] == "2026-04-22T00:00:00Z"
    assert payload["tags"] == ["agent"]
    assert payload["metadata"]["owner"] == "anthropic"
    assert payload["metadata"]["repo"] == "claude-code"
    assert payload["metadata"]["stargazer_count"] == 10
    assert payload["metadata"]["primary_language"] == "Shell"
    assert payload["metadata"]["issue_count"] == 1
    assert payload["output_path"].endswith("anthropic-claude-code/README.md")


def test_save_search_results_writes_markdown_and_jsonl_sidecar(tmp_path: Path) -> None:
    from collect.github import save_search_results

    save_search_results(
        "agent harness",
        tmp_path,
        [
            {
                "name": "agent-harness",
                "owner": {"login": "example"},
                "description": "Evaluate agent runtimes",
                "url": "https://github.com/example/agent-harness",
                "stargazersCount": 42,
            },
            {
                "name": "agent-lab",
                "owner": {"login": "example"},
                "description": "Agent experiments",
                "url": "https://github.com/example/agent-lab",
                "stargazersCount": 7,
            },
        ],
    )

    result_dir = tmp_path / "agent-harness"
    markdown_path = result_dir / "search.md"
    sidecar_path = result_dir / "research-items.jsonl"

    assert markdown_path.exists()
    assert sidecar_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Search: agent harness" in markdown
    assert "## [agent-harness](https://github.com/example/agent-harness)" in markdown

    payloads = [
        json.loads(line)
        for line in sidecar_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(payloads) == 2
    assert payloads[0]["source"] == "github"
    assert payloads[0]["item_type"] == "search-result"
    assert payloads[0]["title"] == "agent-harness"
    assert payloads[0]["canonical_url"] == "https://github.com/example/agent-harness"
    assert payloads[0]["summary"] == "Evaluate agent runtimes"
    assert payloads[0]["metadata"]["query"] == "agent harness"
    assert payloads[0]["metadata"]["owner"] == "example"
    assert payloads[0]["metadata"]["repo"] == "agent-harness"
    assert payloads[0]["metadata"]["stargazer_count"] == 42


def test_save_papers_writes_markdown_and_research_item_sidecar(tmp_path: Path) -> None:
    from collect.papers import save_papers

    paper = {
        "title": "Agent Harness Study",
        "authors": ["Ada Lovelace", "Grace Hopper"],
        "summary": "A benchmark for evaluating agent harness quality.",
        "published": "2026-05-08T00:00:00Z",
        "updated": "2026-05-09T00:00:00Z",
        "arxiv_id": "2605.00001",
        "pdf_url": "https://arxiv.org/pdf/2605.00001",
        "abs_url": "https://arxiv.org/abs/2605.00001",
        "categories": ["cs.AI", "cs.CL"],
    }

    save_papers([paper], "cs.AI", tmp_path)

    category_dir = tmp_path / "arXiv-cs.AI"
    markdown_path = category_dir / "01-Agent Harness Study.md"
    sidecar_path = category_dir / "01-Agent Harness Study.research-item.json"

    assert markdown_path.exists()
    assert sidecar_path.exists()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Agent Harness Study" in markdown
    assert "> **Authors:** Ada Lovelace, Grace Hopper" in markdown

    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert payload["source"] == "papers"
    assert payload["item_type"] == "paper"
    assert payload["title"] == "Agent Harness Study"
    assert payload["authors"] == ["Ada Lovelace", "Grace Hopper"]
    assert payload["summary"] == "A benchmark for evaluating agent harness quality."
    assert payload["canonical_url"] == "https://arxiv.org/abs/2605.00001"
    assert payload["published_at"] == "2026-05-08T00:00:00Z"
    assert payload["updated_at"] == "2026-05-09T00:00:00Z"
    assert payload["discovered_at"] is not None
    assert payload["signal_role"] == "evidence"
    assert payload["discovery_method"] == "arxiv-category"
    assert payload["tags"] == ["cs.AI", "cs.CL"]
    assert payload["metadata"]["pdf_url"] == "https://arxiv.org/pdf/2605.00001"
    assert payload["output_path"].endswith("arXiv-cs.AI/01-Agent Harness Study.md")


@pytest.mark.wechat
def test_fetch_article_writes_markdown_images_and_research_item_sidecar(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import collect.wechat as wechat

    url = "https://mp.weixin.qq.com/s/example"
    html = """
    <html>
      <body>
        <h1 id="activity-name">Harness</h1>
        <span id="js_name">Station</span>
        <script>var create_time = "1700000000";</script>
        <div id="js_content">
          <p>Body summary line</p>
          <img data-src="https://example.com/1.png" />
        </div>
      </body>
    </html>
    """

    class FakePage:
        async def goto(self, target_url: str, wait_until: str) -> None:
            assert target_url == url
            assert wait_until == "domcontentloaded"

        async def wait_for_selector(self, selector: str, timeout: int) -> None:
            assert selector == "#js_content"
            assert timeout == 10000

        async def content(self) -> str:
            return html

    class FakeBrowser:
        async def new_page(self) -> FakePage:
            return FakePage()

    class FakeAsyncCamoufox:
        def __init__(self, headless: bool) -> None:
            assert headless is True

        async def __aenter__(self) -> FakeBrowser:
            return FakeBrowser()

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

    camoufox = ModuleType("camoufox")
    camoufox_async = ModuleType("camoufox.async_api")
    camoufox_async.AsyncCamoufox = FakeAsyncCamoufox
    camoufox.async_api = camoufox_async
    monkeypatch.setitem(sys.modules, "camoufox", camoufox)
    monkeypatch.setitem(sys.modules, "camoufox.async_api", camoufox_async)

    async def no_sleep(seconds: int) -> None:
        assert seconds == 2

    async def fake_download_all_images(img_urls: list[str], img_dir: Path) -> dict[str, str]:
        assert img_urls == ["https://example.com/1.png"]
        img_dir.mkdir(parents=True, exist_ok=True)
        img_dir.joinpath("img_001.png").write_bytes(b"image")
        return {"https://example.com/1.png": "images/img_001.png"}

    monkeypatch.setattr(wechat.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(wechat, "download_all_images", fake_download_all_images)
    monkeypatch.setattr(
        wechat,
        "convert_to_markdown",
        lambda content_html, code_blocks: "Body summary line\n\n![](https://example.com/1.png)",
    )

    asyncio.run(wechat.fetch_article(url, output_dir=tmp_path))

    article_dir = tmp_path / "Harness"
    markdown_path = article_dir / "Harness.md"
    sidecar_path = article_dir / "research-item.json"

    assert markdown_path.exists()
    assert article_dir.joinpath("images", "img_001.png").exists()
    assert sidecar_path.exists()

    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# Harness" in markdown
    assert f"> 原文链接: {url}" in markdown
    assert "![](images/img_001.png)" in markdown

    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    assert payload["source"] == "wechat"
    assert payload["item_type"] == "article"
    assert payload["title"] == "Harness"
    assert payload["canonical_url"] == url
    assert payload["authors"] == ["Station"]
    assert payload["published_at"] == "2023-11-15 06:13:20"
    assert payload["summary"] == "Body summary line"
    assert payload["metadata"]["publisher"] == "Station"
    assert payload["metadata"]["body_length"] > 0
