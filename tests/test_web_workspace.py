from __future__ import annotations

import json
import os
from pathlib import Path

from library.items import ResearchItem
from publish.obsidian import write_markdown


def _write_markdown(path: Path, title: str, body: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = f"# {title}\n\n{body}".rstrip() + "\n"
    path.write_text(content, encoding="utf-8")
    return path


def _write_item(path: Path, item: ResearchItem, markdown_title: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(item.to_json() + "\n", encoding="utf-8")
    if markdown_title and item.output_path:
        _write_markdown(path.parents[0] / Path(item.output_path).name, markdown_title, item.summary or "")


def _write_items_jsonl(path: Path, items: list[ResearchItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(item.to_dict(), ensure_ascii=False) for item in items)
    path.write_text(payload + "\n", encoding="utf-8")
    for item in items:
        if item.output_path:
            _write_markdown(path.parent / Path(item.output_path).name, item.title, item.summary or "")


def _seed_output_tree(output_root: Path) -> None:
    _write_item(
        output_root / "github" / "anthropic-claude-code" / "research-item.json",
        ResearchItem(
            source="github",
            item_type="repository",
            title="Claude Code",
            canonical_url="https://github.com/anthropic/claude-code",
            summary="Agentic coding assistant for terminal workflows",
            updated_at="2026-05-09",
            tags=["agent", "cli"],
            output_path="output/github/anthropic-claude-code/README.md",
        ),
        markdown_title="Claude Code",
    )
    _write_items_jsonl(
        output_root / "github" / "ai-agents" / "research-items.jsonl",
        [
            ResearchItem(
                source="github",
                item_type="search-result",
                title="agent-flow",
                canonical_url="https://github.com/example/agent-flow",
                summary="Real-time visualization for agent orchestration",
                tags=["agent", "visualization"],
                updated_at="2026-05-08",
                output_path="output/github/ai-agents/search.md",
            )
        ],
    )
    _write_item(
        output_root / "papers" / "arXiv-cs.AI" / "01-agent-harness.research-item.json",
        ResearchItem(
            source="papers",
            item_type="paper",
            title="Agent Harness Benchmark",
            canonical_url="https://arxiv.org/abs/2605.00001",
            summary="A benchmark for evaluating agent harness quality.",
            authors=["Ada Lovelace"],
            published_at="2026-05-08",
            tags=["cs.AI", "benchmark"],
            output_path="output/papers/arXiv-cs.AI/01-agent-harness.md",
        ),
        markdown_title="Agent Harness Benchmark",
    )
    _write_item(
        output_root / "wechat" / "agent-harness" / "research-item.json",
        ResearchItem(
            source="wechat",
            item_type="article",
            title="Agent Harness 综述",
            canonical_url="https://mp.weixin.qq.com/s/example",
            summary="Harness overview for AI coding agents.",
            authors=["架构师"],
            published_at="2026-05-01 12:00:00",
            tags=["agent", "wechat"],
            output_path="output/wechat/agent-harness/agent-harness.md",
        ),
        markdown_title="Agent Harness 综述",
    )


def _seed_briefings(output_root: Path) -> None:
    digest_path = write_markdown(
        output_root / "briefing" / "digests" / "ai-weekly.md",
        "# Digest: AI Weekly\n\nRecent highlights\n",
    )
    os.utime(digest_path, (1_700_000_000, 1_700_000_000))

    reading_list_path = write_markdown(
        output_root / "briefing" / "reading-lists" / "ai-agents.md",
        "# Reading List: AI Agents\n\nQueued items\n",
    )
    os.utime(reading_list_path, (1_800_000_000, 1_800_000_000))


def test_workspace_sections_match_phase_one_scope() -> None:
    from workspace_web.service import workspace_sections

    assert workspace_sections() == [
        {"id": "dashboard", "label": "Dashboard"},
        {"id": "library", "label": "Library"},
        {"id": "briefing", "label": "Briefing Workspace"},
    ]


def test_build_dashboard_overview_summarizes_local_archive_and_recent_briefings(tmp_path: Path) -> None:
    from workspace_web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    _seed_briefings(output_root)

    overview = build_dashboard_overview(output_root)

    assert overview["total_items"] == 4
    assert overview["source_counts"] == {"github": 2, "papers": 1, "wechat": 1}
    assert [entry["title"] for entry in overview["recent_briefings"]][:2] == ["Reading List: AI Agents", "Digest: AI Weekly"]


def test_build_dashboard_overview_reports_missing_sources_and_orphan_markdown(tmp_path: Path) -> None:
    from workspace_web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    _write_item(
        output_root / "github" / "sample-repo" / "research-item.json",
        ResearchItem(
            source="github",
            item_type="repository",
            title="Sample Repo",
            canonical_url="https://github.com/example/sample-repo",
            summary="Sample repo summary",
            output_path="output/github/sample-repo/README.md",
        ),
        markdown_title="Sample Repo",
    )
    _write_markdown(output_root / "wechat" / "orphan-article" / "orphan-article.md", "Orphan Article", "No sidecar")

    overview = build_dashboard_overview(output_root)

    assert overview["missing_sources"] == ["papers", "wechat"]
    assert len(overview["orphan_markdown_paths"]) == 1
    assert overview["orphan_markdown_paths"][0].endswith("output/wechat/orphan-article/orphan-article.md")


def test_list_library_items_uses_local_filters_without_remote_collection(tmp_path: Path, monkeypatch) -> None:
    import collect.github as github_collect
    import collect.wechat as wechat_collect
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    monkeypatch.setattr(github_collect, "run_gh", lambda cmd: (_ for _ in ()).throw(AssertionError("remote GitHub fetch should not run")))
    monkeypatch.setattr(wechat_collect, "fetch_article", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remote WeChat fetch should not run")))

    items = list_library_items(output_root, keyword="agent", sources=["github"], since="2026-05-07")

    assert [item["title"] for item in items] == ["Claude Code", "agent-flow"]
    assert {item["source"] for item in items} == {"github"}


def test_get_library_item_detail_maps_local_metadata(tmp_path: Path) -> None:
    from workspace_web.service import get_library_item_detail

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    detail = get_library_item_detail(output_root, "output/wechat/agent-harness/agent-harness.md")

    assert detail is not None
    assert detail["title"] == "Agent Harness 综述"
    assert detail["source"] == "wechat"
    assert detail["authors"] == ["架构师"]
    assert detail["canonical_url"] == "https://mp.weixin.qq.com/s/example"
    assert detail["output_path"] == "output/wechat/agent-harness/agent-harness.md"


def test_preview_briefing_returns_markdown_without_writing_file(tmp_path: Path) -> None:
    from workspace_web.service import preview_briefing

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    preview = preview_briefing(
        output_root,
        mode="digest",
        keyword="agent",
        title="AI Agents",
        sources=["github", "papers"],
    )

    assert preview["title"] == "AI Agents"
    assert "# Digest: AI Agents" in preview["content"]
    assert not (output_root / "briefing" / "digests" / "ai-agents.md").exists()


def test_save_briefing_writes_output_and_marks_missing_sources(tmp_path: Path) -> None:
    from workspace_web.service import save_briefing

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    saved = save_briefing(
        output_root,
        mode="digest",
        keyword="agent",
        title="Weekly AI Brief",
        sources=["github", "papers", "wechat", "twitter"],
    )

    assert saved["path"].endswith("output/briefing/digests/weekly-ai-brief.md")
    assert Path(saved["path"]).exists()
    assert "Missing sources: twitter" in Path(saved["path"]).read_text(encoding="utf-8")


def test_workspace_operator_surface_supports_local_web_entrypoint(tmp_path: Path, monkeypatch) -> None:
    from research.cli import main

    output_root = tmp_path / "output"
    calls: list[Path] = []

    monkeypatch.setattr("research.cli.run_web_workspace", lambda current_output_root: calls.append(current_output_root))

    assert main(["web", "--output-root", str(output_root)]) == 0
    assert calls == [output_root]