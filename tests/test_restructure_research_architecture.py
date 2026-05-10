from __future__ import annotations

import importlib.util
import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType

from library.items import ResearchItem


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_item(path: Path, item: ResearchItem) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(item.to_json() + "\n", encoding="utf-8")


def _write_items_jsonl(path: Path, items: list[ResearchItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(item.to_json().replace("\n", " ") for item in items)
    path.write_text(payload + "\n", encoding="utf-8")


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
        ),
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
        ),
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
        ),
    )


def _load_module(module_name: str, file_path: Path, stub_modules: dict[str, ModuleType] | None = None):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    with _patched_modules(stub_modules or {}):
        spec.loader.exec_module(module)
    return module


@contextmanager
def _patched_modules(stub_modules: dict[str, ModuleType]):
    original = {}
    try:
        for name, module in stub_modules.items():
            original[name] = sys.modules.get(name)
            sys.modules[name] = module
        yield
    finally:
        for name, module in stub_modules.items():
            previous = original[name]
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def _wechat_dependency_stubs() -> dict[str, ModuleType]:
    httpx = ModuleType("httpx")
    httpx.AsyncClient = object

    markdownify = ModuleType("markdownify")
    markdownify.markdownify = lambda *args, **kwargs: ""

    bs4 = ModuleType("bs4")

    class DummySoup:
        pass

    bs4.BeautifulSoup = DummySoup

    camoufox = ModuleType("camoufox")
    camoufox_async = ModuleType("camoufox.async_api")

    class DummyAsyncCamoufox:
        pass

    camoufox_async.AsyncCamoufox = DummyAsyncCamoufox
    camoufox.async_api = camoufox_async

    return {
        "httpx": httpx,
        "markdownify": markdownify,
        "bs4": bs4,
        "camoufox": camoufox,
        "camoufox.async_api": camoufox_async,
    }


def test_library_query_supports_cross_source_and_optional_time_filters(tmp_path: Path) -> None:
    from library.query import query_research_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    all_matches = query_research_items(output_root, keyword="agent")
    assert {item.title for item in all_matches} == {
        "Claude Code",
        "agent-flow",
        "Agent Harness Benchmark",
        "Agent Harness 综述",
    }

    github_only = query_research_items(output_root, keyword="agent", sources=["github"])
    assert {item.source for item in github_only} == {"github"}
    assert {item.title for item in github_only} == {"Claude Code", "agent-flow"}

    recent_only = query_research_items(output_root, keyword="agent", since="2026-05-07")
    assert {item.title for item in recent_only} == {"Claude Code", "Agent Harness Benchmark"}


def test_briefing_reports_generate_obsidian_friendly_markdown(tmp_path: Path) -> None:
    from briefing.reports import write_digest_report, write_reading_list_report
    from library.query import query_research_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    items = query_research_items(output_root, keyword="agent")

    digest_path = write_digest_report(output_root, title="AI Agents", items=items)
    digest = digest_path.read_text(encoding="utf-8")
    assert digest_path == output_root / "briefing" / "digests" / "ai-agents.md"
    assert "# Digest: AI Agents" in digest
    assert "## github" in digest
    assert "[Claude Code](https://github.com/anthropic/claude-code)" in digest

    reading_list_path = write_reading_list_report(output_root, title="AI Agents", items=items)
    reading_list = reading_list_path.read_text(encoding="utf-8")
    assert reading_list_path == output_root / "briefing" / "reading-lists" / "ai-agents.md"
    assert "# Reading List: AI Agents" in reading_list
    assert "- [ ] [Claude Code](https://github.com/anthropic/claude-code)" in reading_list


def test_briefing_reports_allow_partial_success_with_explicit_source_gap(tmp_path: Path) -> None:
    from briefing.reports import write_digest_report
    from library.query import query_research_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    items = query_research_items(output_root, sources=["github", "papers"])

    digest_path = write_digest_report(
        output_root,
        title="Weekly AI Brief",
        items=items,
        requested_sources=["github", "papers", "wechat"],
    )

    digest = digest_path.read_text(encoding="utf-8")
    assert digest_path.exists()
    assert "Missing sources: wechat" in digest
    assert "# Digest: Weekly AI Brief" in digest


def test_workspace_operator_surface_dispatches_collect_actions(tmp_path: Path, monkeypatch) -> None:
    from research.cli import main

    output_root = tmp_path / "output"
    calls: list[tuple[str, object]] = []

    monkeypatch.setattr(
        "research.cli.collect_github_targets",
        lambda targets, output_root, search=False: calls.append(("github", (targets, output_root, search))),
    )
    monkeypatch.setattr(
        "research.cli.collect_paper_categories",
        lambda categories, output_root, max_results=10: calls.append(("papers", (categories, output_root, max_results))),
    )

    async def fake_collect_wechat(url: str, output_root: Path) -> None:
        calls.append(("wechat", (url, output_root)))

    monkeypatch.setattr("research.cli.collect_wechat_article", fake_collect_wechat)

    assert main(["collect", "github", "anthropic/claude-code", "--output-root", str(output_root)]) == 0
    assert main(["collect", "papers", "cs.AI", "--max", "3", "--output-root", str(output_root)]) == 0
    assert main(["collect", "wechat", "https://mp.weixin.qq.com/s/example", "--output-root", str(output_root)]) == 0

    assert calls == [
        ("github", (["anthropic/claude-code"], output_root, False)),
        ("papers", (["cs.AI"], output_root, 3)),
        ("wechat", ("https://mp.weixin.qq.com/s/example", output_root)),
    ]


def test_workspace_operator_surface_supports_query_briefing_and_backfill(tmp_path: Path, capsys) -> None:
    from research.cli import main

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    assert main(["query", "agent", "--output-root", str(output_root)]) == 0
    query_stdout = capsys.readouterr().out
    assert "Claude Code" in query_stdout
    assert "Agent Harness Benchmark" in query_stdout

    assert main(["briefing", "digest", "agent", "--output-root", str(output_root)]) == 0
    digest_path = output_root / "briefing" / "digests" / "agent.md"
    assert digest_path.exists()

    repo_sample = REPO_ROOT / "output" / "github" / "anthropics-claude-code" / "README.md"
    paper_sample = REPO_ROOT / "output" / "papers" / "arXiv-cs.AI" / "01-Personalized Worked Example Generation from Studen.md"
    wechat_sample = (
        REPO_ROOT
        / "output"
        / "wechat"
        / "Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远"
        / "Agent Harness 综述：同一个模型，为什么做出来的 Agent 差这么远.md"
    )

    raw_output_root = tmp_path / "raw-output"
    github_dir = raw_output_root / "github" / "anthropics-claude-code"
    papers_dir = raw_output_root / "papers" / "arXiv-cs.AI"
    wechat_dir = raw_output_root / "wechat" / "agent-harness"
    github_dir.mkdir(parents=True)
    papers_dir.mkdir(parents=True)
    wechat_dir.mkdir(parents=True)
    github_dir.joinpath("README.md").write_text(repo_sample.read_text(encoding="utf-8"), encoding="utf-8")
    papers_dir.joinpath("01-sample.md").write_text(paper_sample.read_text(encoding="utf-8"), encoding="utf-8")
    wechat_dir.joinpath("agent-harness.md").write_text(wechat_sample.read_text(encoding="utf-8"), encoding="utf-8")

    assert main(["backfill", str(raw_output_root)]) == 0
    assert (github_dir / "research-item.json").exists()
    assert (papers_dir / "01-sample.research-item.json").exists()
    assert (wechat_dir / "research-item.json").exists()


def test_workspace_operator_surface_continues_with_partial_briefing_results(tmp_path: Path) -> None:
    from research.cli import main

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    assert (
        main(
            [
                "briefing",
                "digest",
                "agent",
                "--source",
                "github",
                "--source",
                "papers",
                "--source",
                "wechat",
                "--source",
                "twitter",
                "--output-root",
                str(output_root),
            ]
        )
        == 0
    )

    digest_path = output_root / "briefing" / "digests" / "agent.md"
    digest = digest_path.read_text(encoding="utf-8")
    assert "Missing sources: twitter" in digest


def test_legacy_entrypoint_runtime_files_are_removed() -> None:
    assert not (REPO_ROOT / "github-tools" / "fetch_github.py").exists()
    assert not (REPO_ROOT / "papers-tools" / "fetch_papers.py").exists()
    assert not (REPO_ROOT / "wechat-article-to-markdown" / "wechat_article_to_markdown.py").exists()
    assert not (REPO_ROOT / "research_item.py").exists()


def test_legacy_source_tool_directories_are_moved_out_of_repo_root() -> None:
    assert not (REPO_ROOT / "github-tools").exists()
    assert not (REPO_ROOT / "papers-tools").exists()
    assert not (REPO_ROOT / "wechat-article-to-markdown").exists()
    assert not (REPO_ROOT / "twitter-tools").exists()

    tools_dir = REPO_ROOT / "tools"
    assert tools_dir.exists()
    assert (tools_dir / "github" / "README.md").exists()
    assert (tools_dir / "github" / "SKILL.md").exists()
    assert (tools_dir / "papers" / "README.md").exists()
    assert (tools_dir / "papers" / "SKILL.md").exists()
    assert (tools_dir / "twitter" / "README.md").exists()
    assert (tools_dir / "wechat" / "README.md").exists()
    assert (tools_dir / "wechat" / "SKILL.md").exists()
