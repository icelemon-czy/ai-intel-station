from __future__ import annotations

import json
import shutil
from pathlib import Path

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
    assert item.tags == ["agent", "cli"]
    assert item.metadata["owner"] == "anthropic"
    assert item.metadata["repo"] == "claude-code"
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
    assert paper_item.canonical_url == "https://arxiv.org/abs/2604.24758v1"

    assert wechat_item.source == "wechat"
    assert wechat_item.item_type == "article"
    assert wechat_item.canonical_url == "https://mp.weixin.qq.com/s/h49UiGERvz8BMkMW0_4Gwg"


def test_backfill_output_tree_writes_expected_sidecars(tmp_path: Path) -> None:
    output_root = tmp_path / "output"

    repo_dir = output_root / "github" / "anthropics-claude-code"
    repo_dir.mkdir(parents=True)
    shutil.copy2(GITHUB_REPO_SAMPLE, repo_dir / "README.md")

    search_dir = output_root / "github" / "claude-code-agent"
    search_dir.mkdir(parents=True)
    shutil.copy2(GITHUB_SEARCH_SAMPLE, search_dir / "search.md")

    paper_dir = output_root / "papers" / "arXiv-cs.AI"
    paper_dir.mkdir(parents=True)
    paper_md = paper_dir / "01-sample.md"
    shutil.copy2(PAPER_SAMPLE, paper_md)

    wechat_dir = output_root / "wechat" / "sample-article"
    wechat_dir.mkdir(parents=True)
    wechat_md = wechat_dir / "sample-article.md"
    shutil.copy2(WECHAT_SAMPLE, wechat_md)

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