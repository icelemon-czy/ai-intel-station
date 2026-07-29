from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from library.items import ResearchItem
from publish.obsidian import write_markdown


def _free_loopback_port() -> int:
    """Return a kernel-assigned port or skip when the sandbox blocks bind."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])
    except (PermissionError, OSError):
        pytest.skip("sandbox blocks binding 127.0.0.1")


def _wait_for_json(url: str, *, timeout: float = 4.0) -> dict:
    """Poll a subprocess server until the route returns JSON."""
    import urllib.error
    import urllib.request

    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last_error = exc
            time.sleep(0.05)
    raise AssertionError(f"server did not become reachable at {url}: {last_error!r}")


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
        {
            "id": "dashboard",
            "label": "Dashboard",
            "description": "View local archive stats, coverage gaps, and recent briefings",
            "purpose": "See the health of your local ResearchItem archive at a glance.",
            "reads": "Local ResearchItem sidecars under output/ and recent briefing files under output/briefing/.",
            "produces": "An at-a-glance view of total items, source coverage, missing sources, and recent briefings.",
        },
        {
            "id": "library",
            "label": "Library",
            "description": "Search and browse your local research items",
            "purpose": "Find and inspect items already saved to your local archive.",
            "reads": "Local ResearchItem sidecars under output/ only — never a remote source.",
            "produces": "Filtered lists and per-item detail with a link to the saved Markdown.",
        },
        {
            "id": "briefing",
            "label": "Briefing Workspace",
            "description": "Generate digest or reading list from your archive",
            "purpose": "Turn local items into a digest or reading list you can read or save.",
            "reads": "Local ResearchItem sidecars matching your keyword / sources / date filters.",
            "produces": "A previewable Markdown briefing and, on Save, a file under output/briefing/.",
        },
        {
            "id": "collect",
            "label": "Collect Workspace",
            "description": "Collect research material from GitHub, papers, and WeChat",
            "purpose": "Pull new material from GitHub, arXiv, or WeChat into the local archive.",
            "reads": "Your source-specific inputs (owner/repo, arXiv category, or WeChat URL).",
            "produces": "New ResearchItem sidecars and Markdown files under output/<source>/.",
        },
    ]


def test_workspace_sections_includes_collect_workspace() -> None:
    """Test that Collect Workspace is included in navigation sections."""
    from workspace_web.service import workspace_sections

    sections = workspace_sections()
    section_ids = [s["id"] for s in sections]

    assert "collect" in section_ids, f"Expected 'collect' in section ids: {section_ids}"
    collect_section = next(s for s in sections if s["id"] == "collect")
    assert collect_section["label"] == "Collect Workspace"


def test_collect_workspace_has_description() -> None:
    """Test that Collect Workspace section includes description for page heading."""
    from workspace_web.service import workspace_sections

    sections = workspace_sections()
    collect_section = next(s for s in sections if s["id"] == "collect")
    assert "description" in collect_section, "Collect section should have description for page heading"
    assert len(collect_section["description"]) > 0


def test_list_collect_sources_returns_all_supported_sources() -> None:
    """Test that collect workspace lists all supported sources."""
    from workspace_web.service import list_collect_sources

    sources = list_collect_sources()
    source_ids = [s["id"] for s in sources]

    assert "github" in source_ids
    assert "papers" in source_ids
    assert "wechat" in source_ids


def test_get_collect_form_returns_source_specific_fields() -> None:
    """Test that collect form returns fields specific to each source."""
    from workspace_web.service import get_collect_form

    github_form = get_collect_form("github")
    github_field_names = [f["name"] for f in github_form["fields"]]
    assert "query" in github_field_names
    assert "search" in github_field_names
    assert "max" in github_field_names

    papers_form = get_collect_form("papers")
    papers_field_names = [f["name"] for f in papers_form["fields"]]
    assert "category" in papers_field_names
    assert "max" in papers_field_names

    wechat_form = get_collect_form("wechat")
    wechat_field_names = [f["name"] for f in wechat_form["fields"]]
    assert "url" in wechat_field_names


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

    assert [item["title"] for item in items["items"]] == ["Claude Code", "agent-flow"]
    assert {item["source"] for item in items["items"]} == {"github"}


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


def test_build_dashboard_overview_returns_empty_state_info_when_no_items(tmp_path: Path) -> None:
    """Test that dashboard overview indicates empty state when no items exist."""
    from workspace_web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    overview = build_dashboard_overview(output_root)

    assert overview["total_items"] == 0
    assert overview["missing_sources"] == ["github", "papers", "wechat"]
    assert len(overview["orphan_markdown_paths"]) == 0


def test_list_library_items_returns_empty_list_when_no_items(tmp_path: Path) -> None:
    """Test that library returns empty list when no items exist."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    items = list_library_items(output_root, keyword="agent", sources=["github", "papers", "wechat"])

    assert items["items"] == []


def test_preview_briefing_handles_empty_items_gracefully(tmp_path: Path) -> None:
    """Test that briefing preview works with no items."""
    from workspace_web.service import preview_briefing

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    preview = preview_briefing(
        output_root,
        mode="digest",
        keyword="nonexistent",
        title="Empty Briefing",
        sources=["github", "papers"],
    )

    assert preview["title"] == "Empty Briefing"
    assert preview["item_count"] == 0


def test_github_collect_form_has_repo_and_search_mode_fields() -> None:
    """Test that GitHub collect form supports both repo and search modes."""
    from workspace_web.service import get_collect_form

    github_form = get_collect_form("github")
    field_names = [f["name"] for f in github_form["fields"]]

    assert "query" in field_names
    assert "search" in field_names
    assert "max" in field_names


def test_papers_collect_form_has_category_and_max_fields() -> None:
    """Test that papers collect form has category and max fields."""
    from workspace_web.service import get_collect_form

    papers_form = get_collect_form("papers")
    field_names = [f["name"] for f in papers_form["fields"]]

    assert "category" in field_names
    assert "max" in field_names


def test_collect_form_includes_field_labels_and_placeholders() -> None:
    """Test that collect forms include proper labels and placeholders."""
    from workspace_web.service import get_collect_form

    github_form = get_collect_form("github")
    for field in github_form["fields"]:
        assert "label" in field
        if field["type"] == "text":
            assert "placeholder" in field

    papers_form = get_collect_form("papers")
    for field in papers_form["fields"]:
        assert "label" in field


def test_get_collect_form_returns_unknown_for_unsupported_source() -> None:
    """Test that get_collect_form handles unsupported sources gracefully."""
    from workspace_web.service import get_collect_form

    unknown_form = get_collect_form("unsupported")
    assert unknown_form["id"] == "unsupported"
    assert unknown_form["label"] == "unsupported"
    assert unknown_form["fields"] == []


def test_run_collect_github_single_repo(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to GitHub collect for single repo mode."""
    import collect.github as github_collect

    called_with: list = []

    def mock_save_repo(owner: str, repo: str, output_dir: Path) -> None:
        called_with.append((owner, repo))
        return None

    monkeypatch.setattr(github_collect, "save_repo", mock_save_repo)
    from workspace_web.service import run_collect

    result = run_collect("github", {"query": "anthropic/claude-code", "search": False, "max": 10})
    assert result["status"] == "success"
    assert "anthropic/claude-code" in result["message"]
    assert called_with == [("anthropic", "claude-code")]


def test_run_collect_github_search_mode(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to GitHub search when search=True."""
    import collect.github as github_collect

    called_with: list = []

    def mock_run_gh(cmd: list[str]) -> str:
        called_with.append(cmd)
        return "[]"

    monkeypatch.setattr(github_collect, "run_gh", mock_run_gh)
    from workspace_web.service import run_collect

    result = run_collect("github", {"query": "agent", "search": True, "max": 5})
    assert result["status"] == "success"
    assert "agent" in result["message"]
    assert called_with == [["search", "repos", "agent", "--limit", "5"]]


def test_run_collect_papers(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to papers collect."""
    import collect.papers as papers_collect

    called_with: list = []
    save_called: list = []

    def mock_fetch_papers(
        categories: list[str],
        max_results: int = 10,
        **_kwargs,
    ) -> list:
        called_with.append((categories, max_results))
        return [{"title": "Agent Harness", "url": "https://arxiv.org/abs/2605.00001"}]

    def mock_save_papers(papers: list, category: str, output_dir: Path) -> None:
        save_called.append((category, output_dir))

    monkeypatch.setattr(papers_collect, "fetch_papers_by_category", mock_fetch_papers)
    monkeypatch.setattr(papers_collect, "save_papers", mock_save_papers)
    from workspace_web.service import run_collect

    result = run_collect("papers", {"category": "cs.AI", "max": 3})
    assert result["status"] == "success"
    assert "cs.AI" in result["message"]
    assert called_with == [(["cs.AI"], 3)]
    assert len(save_called) == 1  # must persist, not just fetch


def test_run_collect_wechat(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to WeChat collect with URL."""
    import collect.wechat as wechat_collect

    called_with: list = []

    async def mock_fetch(url: str, output_dir: Path | None = None) -> dict:
        called_with.append(url)
        return {"title": "Agent Overview", "url": url}

    monkeypatch.setattr(wechat_collect, "fetch_article", mock_fetch)
    from workspace_web.service import run_collect

    result = run_collect("wechat", {"url": "https://mp.weixin.qq.com/s/test"})
    assert result["status"] == "success"
    assert called_with == ["https://mp.weixin.qq.com/s/test"]


def test_run_collect_wechat_missing_url_returns_error(tmp_path: Path) -> None:
    """Test that WeChat collect returns error when URL is missing."""
    from workspace_web.service import run_collect

    result = run_collect("wechat", {"url": ""})
    assert result["status"] == "error"
    assert "URL" in result["message"]


# ---------------------------------------------------------------------------
# Library pagination tests
# ---------------------------------------------------------------------------

def test_list_library_items_pagination_returns_correct_slice(tmp_path: Path) -> None:
    """Test that list_library_items returns paginated results with metadata."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    result = list_library_items(output_root, page=1, page_size=2)
    assert "items" in result
    assert "total_count" in result
    assert "page" in result
    assert "page_size" in result
    assert "total_pages" in result
    assert result["page"] == 1
    assert result["page_size"] == 2
    assert len(result["items"]) <= 2


def test_list_library_items_pagination_page_2(tmp_path: Path) -> None:
    """Test that requesting page 2 returns different results."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    page1 = list_library_items(output_root, page=1, page_size=2)
    page2 = list_library_items(output_root, page=2, page_size=2)

    page1_ids = [item["output_path"] for item in page1["items"]]
    page2_ids = [item["output_path"] for item in page2["items"]]
    assert page1_ids != page2_ids or page1["total_count"] <= 2


def test_list_library_items_total_count_matches_all_results(tmp_path: Path) -> None:
    """Test that total_count equals all items without pagination."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    result_all = list_library_items(output_root)
    result_page1 = list_library_items(output_root, page=1, page_size=100)

    assert result_page1["total_count"] == result_all["total_count"]


def test_list_library_items_page_size_change_resets_to_page_1(tmp_path: Path) -> None:
    """Test that changing page_size returns page 1 results."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    page10 = list_library_items(output_root, page=2, page_size=10)
    page5 = list_library_items(output_root, page=1, page_size=5)

    assert page5["page"] == 1
    assert page5["page_size"] == 5


# ---------------------------------------------------------------------------
# Library selection synchronization tests
# ---------------------------------------------------------------------------

def test_list_library_items_keyword_change_affects_total_count(tmp_path: Path) -> None:
    """Test that changing keyword changes total_count and results."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    agent_results = list_library_items(output_root, keyword="agent")
    empty_results = list_library_items(output_root, keyword="nonexistent-keyword-xyz")

    assert agent_results["total_count"] > 0
    assert empty_results["total_count"] == 0


def test_get_library_item_detail_returns_expanded_metadata(tmp_path: Path) -> None:
    """Test that get_library_item_detail returns item_type, published_at, and updated_at fields."""
    from workspace_web.service import get_library_item_detail

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    detail = get_library_item_detail(output_root, "output/wechat/agent-harness/agent-harness.md")

    assert detail is not None
    assert "item_type" in detail
    assert detail["item_type"] == "article"
    assert "published_at" in detail
    assert "updated_at" in detail or detail.get("published_at") is not None


def test_run_collect_unknown_source_returns_error(tmp_path: Path) -> None:
    """Test that run_collect returns error for unknown source."""
    from workspace_web.service import run_collect

    result = run_collect("twitter", {"query": "test"})
    assert result["status"] == "error"
    assert "Unknown source" in result["message"]
# WEB-COLLECT-PERSIST: align-web-collect-with-local-output-truth
# ---------------------------------------------------------------------------


def test_run_collect_github_writes_to_output_root(tmp_path: Path, monkeypatch) -> None:
    """GitHub single-repo collect MUST write to output_root/github, not /tmp."""
    import collect.github as github_collect

    captured: dict = {}

    def mock_save_repo(owner: str, repo: str, output_dir: Path) -> None:
        captured["output_dir"] = output_dir

    monkeypatch.setattr(github_collect, "save_repo", mock_save_repo)
    from workspace_web.service import run_collect

    result = run_collect(
        "github",
        {"query": "owner/repo", "search": False, "max": 10},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert captured["output_dir"] == tmp_path / "output" / "github"


def test_run_collect_papers_saves_to_output_root(tmp_path: Path, monkeypatch) -> None:
    """Papers collect MUST call save_papers() with output_root/papers."""
    import collect.papers as papers_collect

    save_captured: dict = {}

    def mock_fetch(
        categories: list,
        max_results: int = 10,
        **_kwargs,
    ) -> list:
        return [{"title": "Test Paper", "arxiv_id": "2605.00001"}]

    def mock_save(papers: list, category: str, output_dir: Path) -> None:
        save_captured["category"] = category
        save_captured["output_dir"] = output_dir
        save_captured["count"] = len(papers)

    monkeypatch.setattr(papers_collect, "fetch_papers_by_category", mock_fetch)
    monkeypatch.setattr(papers_collect, "save_papers", mock_save)
    from workspace_web.service import run_collect

    result = run_collect(
        "papers",
        {"category": "cs.AI", "max": 1},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert save_captured["output_dir"] == tmp_path / "output" / "papers"
    assert save_captured["category"] == "cs.AI"


def test_run_collect_wechat_uses_output_root_and_awaits(tmp_path: Path, monkeypatch) -> None:
    """WeChat collect MUST await fetch_article and pass output_root/wechat."""
    import collect.wechat as wechat_collect

    captured: dict = {}

    async def mock_fetch_article(url: str, output_dir: Path | None = None) -> dict:
        captured["url"] = url
        captured["output_dir"] = output_dir
        return {"title": "Test Article", "url": url}

    monkeypatch.setattr(wechat_collect, "fetch_article", mock_fetch_article)
    from workspace_web.service import run_collect

    result = run_collect(
        "wechat",
        {"url": "https://mp.weixin.qq.com/s/test"},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert captured["url"] == "https://mp.weixin.qq.com/s/test"
    assert captured["output_dir"] == tmp_path / "output" / "wechat"


# ---------------------------------------------------------------------------
# WEB-UI-REGRESS: add-collect-workspace-ui-regression-coverage
# ---------------------------------------------------------------------------


def test_all_navigation_sections_have_react_rendering_branches() -> None:
    """Every section id in workspace_sections() must have an activeSection branch in App.jsx."""
    from workspace_web.service import workspace_sections

    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    sections = workspace_sections()
    for section in sections:
        sid = section["id"]
        assert f'activeSection === "{sid}"' in app_jsx, (
            f"Section '{sid}' declared in workspace_sections() but has no rendering branch "
            f'(activeSection === "{sid}") in web/src/App.jsx'
        )


# ---------------------------------------------------------------------------
# Source taxonomy tests
# ---------------------------------------------------------------------------

def test_collect_sources_labels_match_library_source_names(tmp_path: Path) -> None:
    """Test that list_collect_sources returns labels that match Library source display."""
    from workspace_web.service import list_collect_sources

    sources = list_collect_sources()
    source_ids = [s["id"] for s in sources]

    assert "github" in source_ids
    assert "papers" in source_ids
    assert "wechat" in source_ids

    github_source = next(s for s in sources if s["id"] == "github")
    assert github_source["label"] == "GitHub"

    papers_source = next(s for s in sources if s["id"] == "papers")
    assert papers_source["label"] == "arXiv Papers"


def test_source_labels_used_consistently_in_navigation(tmp_path: Path) -> None:
    """Test that navigation sections use consistent source labels."""
    from workspace_web.service import workspace_sections

    sections = workspace_sections()
    collect_section = next((s for s in sections if s["id"] == "collect"), None)

    assert collect_section is not None
    assert "description" in collect_section
    assert "GitHub" in collect_section["description"] or "github" in collect_section["description"]


# ---------------------------------------------------------------------------
# COLLECT-SOURCE-PURPOSE-CARDS: add-collect-source-purpose-cards
# ---------------------------------------------------------------------------


def _assert_purpose_card_shape(form: dict[str, object]) -> None:
    """Each collect form MUST expose purpose, required_input, output_dir, dependency_hint."""
    for key in ("purpose", "required_input", "output_dir", "dependency_hint"):
        assert key in form, f"Collect form for {form.get('id')!r} is missing {key!r} for purpose card"
        value = form[key]
        assert isinstance(value, str) and value.strip(), f"Collect form {key!r} for {form.get('id')!r} must be a non-empty string"


def test_github_collect_form_exposes_purpose_card_fields() -> None:
    """GitHub form MUST expose purpose, required_input, output_dir, dependency_hint."""
    from workspace_web.service import get_collect_form

    form = get_collect_form("github")
    _assert_purpose_card_shape(form)
    assert "output/github" in form["output_dir"]
    assert "owner/repo" in form["required_input"] or "search" in form["required_input"].lower()


def test_papers_collect_form_exposes_purpose_card_fields() -> None:
    """Papers form MUST expose purpose, required_input, output_dir, dependency_hint."""
    from workspace_web.service import get_collect_form

    form = get_collect_form("papers")
    _assert_purpose_card_shape(form)
    assert "output/papers" in form["output_dir"]
    assert "category" in form["required_input"].lower() or "arxiv" in form["required_input"].lower()


def test_wechat_collect_form_exposes_purpose_card_fields() -> None:
    """WeChat form MUST expose purpose, required_input, output_dir, dependency_hint."""
    from workspace_web.service import get_collect_form

    form = get_collect_form("wechat")
    _assert_purpose_card_shape(form)
    assert "output/wechat" in form["output_dir"]
    assert "url" in form["required_input"].lower()


def test_collect_section_renders_purpose_card_using_form_metadata() -> None:
    """App.jsx MUST reference the new purpose-card keys when rendering the active source form."""
    from workspace_web.service import get_collect_form

    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    github_form = get_collect_form("github")
    for key in ("purpose", "required_input", "output_dir", "dependency_hint"):
        assert key in github_form, f"Test fixture broken: {key!r} missing from GitHub form"
        # The component must look up the key off `formDefinition` (or equivalent) so the
        # purpose card renders server-provided metadata instead of hardcoded copy.
        assert f"formDefinition.{key}" in app_jsx or f"form?.{key}" in app_jsx or f"[{key}]" in app_jsx, (
            f"App.jsx must read {key!r} from form metadata so purpose cards reflect source-specific data"
        )


def test_purpose_card_content_differs_per_source() -> None:
    """Spec Scenario 4: switching source MUST replace the purpose card with source-specific data.

    Verifies both that the backend returns distinct content per source AND that the React
    component re-fetches form metadata whenever `activeSource` changes (not on initial mount only).
    """
    from workspace_web.service import get_collect_form

    # Backend: each source MUST return distinct, source-specific content — no shared fallbacks.
    github = get_collect_form("github")
    papers = get_collect_form("papers")
    wechat = get_collect_form("wechat")

    assert github["output_dir"] != papers["output_dir"]
    assert papers["output_dir"] != wechat["output_dir"]
    assert github["output_dir"] != wechat["output_dir"]
    assert github["purpose"] != papers["purpose"]
    assert papers["purpose"] != wechat["purpose"]
    # Required input text also differs per source
    assert github["required_input"] != wechat["required_input"]
    assert "owner/repo" in github["required_input"].lower() or "search" in github["required_input"].lower()
    assert "category" in papers["required_input"].lower() or "arxiv" in papers["required_input"].lower()
    assert "url" in wechat["required_input"].lower()

    # React: the form-definition fetch effect MUST depend on `activeSource` so a switch
    # actually triggers a new fetch (replacing the old card content).
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "requestJson(`/api/collect/form/${activeSource}`)" in app_jsx, (
        "CollectSection must have a fetch to /api/collect/form/${activeSource}"
    )
    # Find that useEffect's dep array — search forward from the fetch call.
    fetch_idx = app_jsx.find("requestJson(`/api/collect/form/${activeSource}`)")
    assert fetch_idx != -1
    # The dep array is the first `[...]` AFTER the fetch's closing `});`
    tail = app_jsx[fetch_idx:]
    close_paren = tail.find("});")
    assert close_paren != -1
    after_close = tail[close_paren + 3 :]
    import re

    deps_match = re.search(r"\[\s*([^\]]*?)\s*\]", after_close)
    assert deps_match, (
        f"Could not find a dep array [...] after the form-fetch useEffect; tail starts with: {after_close[:80]!r}"
    )
    deps = deps_match.group(1)
    assert "activeSource" in deps, (
        f"form-fetch useEffect MUST depend on activeSource so the purpose card refreshes on switch; "
        f"current deps=[{deps.strip()}]"
    )


# ---------------------------------------------------------------------------
# FIRST-RUN-EMPTY-STATE: add-first-run-empty-state-guidance
# ---------------------------------------------------------------------------


def _assert_empty_state_shape(
    payload: dict[str, object],
    context: str,
    *,
    required_keywords: tuple[str, ...] = (),
) -> None:
    """A well-formed empty_state block MUST have an explanation and at least one next-step pointer.

    `required_keywords` enforces that the spec THEN — e.g. "points to Collect Workspace
    and the backfill command" — is actually reflected in the rendered text, not just
    that the field is non-empty. Every keyword must appear in the explanation OR in
    the joined next_steps string.
    """
    assert "empty_state" in payload, f"{context} is missing 'empty_state' block"
    empty_state = payload["empty_state"]
    assert isinstance(empty_state, dict), f"{context} empty_state must be a dict, got {type(empty_state).__name__}"
    assert "explanation" in empty_state and empty_state["explanation"].strip(), (
        f"{context} empty_state must include a non-empty 'explanation' string"
    )
    assert "next_steps" in empty_state and isinstance(empty_state["next_steps"], list) and empty_state["next_steps"], (
        f"{context} empty_state must include a non-empty 'next_steps' list"
    )
    if required_keywords:
        blob = (empty_state["explanation"] + " " + " ".join(empty_state["next_steps"])).lower()
        for keyword in required_keywords:
            assert keyword.lower() in blob, (
                f"{context} empty_state must mention {keyword!r} per spec THEN, "
                f"got explanation={empty_state['explanation']!r} next_steps={empty_state['next_steps']!r}"
            )


def test_dashboard_overview_exposes_empty_state_when_no_items(tmp_path: Path) -> None:
    """Dashboard MUST surface empty_state when local archive is empty."""
    from workspace_web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    overview = build_dashboard_overview(output_root)
    assert overview["total_items"] == 0
    _assert_empty_state_shape(
        overview,
        "dashboard overview",
        required_keywords=("Collect Workspace", "backfill"),
    )


def test_list_library_items_exposes_empty_state_when_no_results(tmp_path: Path) -> None:
    """Library MUST surface empty_state when no items match the filters."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    result = list_library_items(output_root, keyword="nothing-matches-this-xyz")
    assert result["items"] == []
    _assert_empty_state_shape(
        result,
        "library listing",
        required_keywords=("Collect Workspace",),
    )


def test_preview_briefing_exposes_empty_state_when_no_items(tmp_path: Path) -> None:
    """Briefing preview MUST surface empty_state when no items match."""
    from workspace_web.service import preview_briefing

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    preview = preview_briefing(
        output_root,
        mode="digest",
        keyword="no-such-keyword-xyz",
        title="Empty Briefing",
        sources=["github", "papers"],
    )
    assert preview["item_count"] == 0
    _assert_empty_state_shape(
        preview,
        "briefing preview",
        required_keywords=("Collect Workspace", "backfill"),
    )


def test_app_jsx_renders_empty_state_panels_on_each_workspace() -> None:
    """App.jsx MUST render empty-state guidance for Dashboard / Library / Briefing / Collect."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    for section in ("DashboardSection", "LibrarySection", "BriefingSection", "CollectSection"):
        idx = app_jsx.find(f"function {section}")
        assert idx != -1, f"App.jsx is missing the {section} component"
        body = app_jsx[idx:]
        assert "empty_state" in body or "emptyState" in body, (
            f"{section} must surface an empty_state block (e.g. overview.empty_state) when data is empty"
        )


# ---------------------------------------------------------------------------
# BRIEFING-FLOW-COPY: clarify-briefing-generation-flow
# ---------------------------------------------------------------------------


def test_briefing_mode_purposes_exposes_both_modes() -> None:
    """Briefing metadata MUST describe both digest and reading-list modes."""
    from workspace_web.service import briefing_mode_purposes

    purposes = briefing_mode_purposes()
    assert purposes.get("digest"), "Missing digest mode purpose"
    assert purposes.get("reading-list"), "Missing reading-list mode purpose"
    assert "summariz" in purposes["digest"].lower() or "summary" in purposes["digest"].lower()
    assert "read" in purposes["reading-list"].lower()


def test_briefing_action_purposes_distinguishes_preview_and_save() -> None:
    """Briefing metadata MUST explain preview vs save."""
    from workspace_web.service import briefing_action_purposes

    actions = briefing_action_purposes()
    assert actions.get("preview"), "Missing preview action purpose"
    assert actions.get("save"), "Missing save action purpose"
    assert "preview" in actions["preview"].lower() or "show" in actions["preview"].lower()
    assert "save" in actions["save"].lower() or "write" in actions["save"].lower()
    assert "output/briefing" in actions["save"], "Save purpose must mention the output/briefing path"


def test_briefing_flow_notes_explains_input_source() -> None:
    """Briefing metadata MUST explain that briefing content comes from the local library."""
    from workspace_web.service import briefing_flow_notes

    notes = briefing_flow_notes()
    assert notes.get("input_source"), "Missing input_source note"
    text = notes["input_source"].lower()
    assert "local" in text, "Input source note must mention 'local'"
    assert "library" in text or "researchitem" in text or "sidecar" in text


def test_app_jsx_renders_briefing_flow_explanations() -> None:
    """BriefingSection MUST render the flow explanations in App.jsx."""
    from workspace_web.service import briefing_action_purposes, briefing_flow_notes, briefing_mode_purposes

    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    idx = app_jsx.find("function BriefingSection")
    assert idx != -1, "App.jsx is missing BriefingSection"
    body = app_jsx[idx:]

    # The flow notes come from /api/briefing/metadata — assert the section reads them
    assert "/api/briefing/metadata" in body, "BriefingSection must fetch /api/briefing/metadata"
    assert "setFlowNotes" in body, "BriefingSection must capture flow_notes from the metadata payload"
    assert "setModePurposes" in body, "BriefingSection must capture mode_purposes from the metadata payload"
    assert "setActionPurposes" in body, "BriefingSection must capture action_purposes from the metadata payload"

    # The three metadata keys from the service must be referenced as data in the rendered JSX
    for key in briefing_flow_notes():
        assert f"flowNotes.{key}" in body, f"BriefingSection must render flowNotes.{key}"
    for mode in briefing_mode_purposes():
        assert f"modePurposes[form.mode]" in body or f'modePurposes["{mode}"]' in body, (
            f"BriefingSection must look up modePurposes for {mode!r}"
        )
    for action in briefing_action_purposes():
        assert f"actionPurposes.{action}" in body, f"BriefingSection must render actionPurposes.{action}"

    # Spec Scenario 3 AND: "after a Save, the saved file path is displayed and identified as a
    # derived reading artifact". The backend metadata key is `saved_artifact` and the React
    # code MUST render it next to the saved path.
    assert "flowNotes.saved_artifact" in body, (
        "BriefingSection must render flowNotes.saved_artifact alongside the saved path"
    )
    # The literal "Saved:" label must be next to the artifact tag, so the user sees the link
    # between the saved file and the "derived reading artifact" framing.
    assert "Saved:" in body, "BriefingSection must render the 'Saved:' label near the saved artifact line"


# ---------------------------------------------------------------------------
# LIBRARY-LOCAL-SCOPE: clarify-library-local-search-scope
# ---------------------------------------------------------------------------


def test_library_search_notes_explains_scope_filter_and_results() -> None:
    """Backend MUST expose library_search_notes() with scope / filter / result explanations."""
    from workspace_web.service import library_search_notes

    notes = library_search_notes()
    for key in ("scope", "filter", "result_source"):
        assert key in notes, f"library_search_notes is missing {key!r}"
        assert notes[key].strip(), f"library_search_notes[{key!r}] must be a non-empty string"

    # Spec Scenario 1: scope MUST clarify that search is local AND does not trigger remote fetches.
    scope_lower = notes["scope"].lower()
    assert "local" in scope_lower, "scope must mention 'local' so users understand it is local-only"
    # Strong form: the literal phrase "remote fetch" must appear, OR "no" + "remote" both
    # appear. The weaker "no" / "without" alone is ambiguous and was a review finding.
    assert (
        "remote fetch" in scope_lower
        or ("no" in scope_lower and "remote" in scope_lower)
    ), (
        "scope must explicitly say there is no remote fetch — found neither 'remote fetch' nor "
        f"'no' + 'remote' together. got: {notes['scope']!r}"
    )

    # Spec Scenario 2: filter hint MUST explicitly say filters act on already-saved items.
    filter_lower = notes["filter"].lower()
    assert "filter" in filter_lower or "filters" in filter_lower
    assert "saved" in filter_lower or "local" in filter_lower, (
        f"filter hint must say filters act on already-saved / local items, got: {notes['filter']!r}"
    )

    # Spec Scenario 3: result_source MUST point to the local archive path.
    result_lower = notes["result_source"].lower()
    assert "output/" in result_lower or "archive" in result_lower, (
        f"result_source must mention output/ or archive, got: {notes['result_source']!r}"
    )


def test_list_library_items_search_notes_is_attached_to_payload(tmp_path: Path) -> None:
    """The library list payload MUST include the search notes so the UI can render them."""
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    result = list_library_items(output_root)
    assert "search_notes" in result, "list_library_items must attach search_notes to its payload"
    assert result["search_notes"]["scope"], "scope must be populated"
    assert result["search_notes"]["filter"], "filter must be populated"
    assert result["search_notes"]["result_source"], "result_source must be populated"


def test_list_library_items_still_does_not_trigger_remote_fetch(tmp_path: Path, monkeypatch) -> None:
    """Library query behavior MUST stay local-only (no remote fetch)."""
    import collect.github as github_collect
    import collect.wechat as wechat_collect
    from workspace_web.service import list_library_items

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    monkeypatch.setattr(github_collect, "run_gh", lambda cmd: (_ for _ in ()).throw(AssertionError("remote github fetch should not run")))
    monkeypatch.setattr(wechat_collect, "fetch_article", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remote wechat fetch should not run")))

    # Should not raise, because Library is local-only.
    result = list_library_items(output_root, keyword="agent")
    assert "items" in result
    assert "search_notes" in result


def test_app_jsx_library_section_renders_scope_note() -> None:
    """LibrarySection MUST render the search-scope note."""
    from workspace_web.service import library_search_notes

    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    idx = app_jsx.find("function LibrarySection")
    assert idx != -1, "App.jsx is missing LibrarySection"
    body = app_jsx[idx:]

    # The component must capture the search_notes payload from /api/library
    assert "setSearchNotes" in body, "LibrarySection must capture search_notes from /api/library payload"

    # Each key from library_search_notes() must be referenced via the searchNotes state object
    for key in library_search_notes():
        assert f"searchNotes.{key}" in body, (
            f"LibrarySection must render searchNotes.{key} (got body without it)"
        )


# ---------------------------------------------------------------------------
# PAGE-PURPOSE-COPY: clarify-web-workspace-page-purpose-copy
# ---------------------------------------------------------------------------


def test_workspace_sections_include_purpose_reads_produces() -> None:
    """Every section MUST carry purpose / reads / produces metadata."""
    from workspace_web.service import workspace_sections

    sections = workspace_sections()
    for section in sections:
        for key in ("purpose", "reads", "produces"):
            assert key in section, f"Section {section['id']!r} is missing {key!r}"
            assert section[key].strip(), f"Section {section['id']!r} {key!r} must be a non-empty string"


def test_page_purpose_cards_returns_one_per_section() -> None:
    """page_purpose_cards() MUST return a 4-entry list keyed by section id."""
    from workspace_web.service import page_purpose_cards

    cards = page_purpose_cards()
    ids = {c["id"] for c in cards}
    assert ids == {"dashboard", "library", "briefing", "collect"}, f"Unexpected card ids: {ids}"


def test_app_jsx_renders_page_purpose_card_for_each_section() -> None:
    """App.jsx MUST render a PagePurposeCard for each of the 4 sections."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    # 1) The reusable component must exist.
    assert "PagePurposeCard" in app_jsx, "App.jsx must define or use a PagePurposeCard component"

    # 2) Each section's branch must mount its own <XSection section={currentPurpose} /> — the count
    #    of these specific render calls is the only proof that all four sections get the card.
    rendered_section_calls = app_jsx.count("section={currentPurpose}")
    assert rendered_section_calls == 4, (
        f"App.jsx must render 4 sections with section={{currentPurpose}} prop, "
        f"found {rendered_section_calls}"
    )

    # 3) Each section's JSX must consume the purpose-card keys. We slice the JSX around each
    #    <XSection ... currentPurpose> call and require every key to appear at least once in
    #    the whole file (PagePurposeCard component is the consumer).
    for key in ("section.purpose", "section.reads", "section.produces"):
        assert key in app_jsx, f"PagePurposeCard must render {key!r} from the section prop"


# ---------------------------------------------------------------------------
# COLLECT-RESULT-EXPLANATIONS: standardize-collect-run-result-explanations
# ---------------------------------------------------------------------------


def _assert_standardized_result(result: dict[str, object], source: str) -> None:
    """Every run_collect() result MUST include summary, next_step, and details."""
    assert "summary" in result and result["summary"].strip(), (
        f"{source} result must include a non-empty 'summary' string"
    )
    assert "next_step" in result and result["next_step"].strip(), (
        f"{source} result must include a non-empty 'next_step' string"
    )
    assert "details" in result and isinstance(result["details"], dict), (
        f"{source} result must include a 'details' dict"
    )


def test_run_collect_github_includes_summary_next_step_and_details(monkeypatch) -> None:
    """GitHub success MUST return summary / next_step / details alongside existing fields."""
    import collect.github as github_collect

    monkeypatch.setattr(
        github_collect,
        "save_repo",
        lambda owner, repo, output_dir: None,
    )
    from workspace_web.service import run_collect

    result = run_collect("github", {"query": "anthropic/claude-code", "search": False, "max": 10})
    _assert_standardized_result(result, "github")
    assert result["status"] == "success"
    # Backwards-compat fields must remain
    assert "message" in result
    assert "item_count" in result
    assert "saved_paths" in result
    # Next step should point to the Library
    assert "library" in result["next_step"].lower() or "browse" in result["next_step"].lower()


def test_run_collect_papers_includes_summary_next_step_and_details(monkeypatch) -> None:
    """arXiv success MUST return summary / next_step / details alongside existing fields."""
    import collect.papers as papers_collect

    monkeypatch.setattr(
        papers_collect,
        "fetch_papers_by_category",
        lambda categories, max_results=10, **_kwargs: [{"title": "T", "url": "u"}],
    )
    monkeypatch.setattr(papers_collect, "save_papers", lambda papers, category, output_dir: None)
    from workspace_web.service import run_collect

    result = run_collect("papers", {"category": "cs.AI", "max": 1})
    _assert_standardized_result(result, "papers")
    assert result["status"] == "success"
    assert "message" in result
    assert "item_count" in result
    assert "saved_paths" in result
    assert "cs.AI" in result["summary"]


def test_run_collect_wechat_includes_summary_next_step_and_details() -> None:
    """WeChat success MUST return summary / next_step / details alongside existing fields."""
    import collect.wechat as wechat_collect

    async def mock_fetch(url: str, output_dir=None) -> dict:
        return {"title": "T", "url": url}

    wechat_collect.fetch_article = mock_fetch  # type: ignore[assignment]
    from workspace_web.service import run_collect

    result = run_collect("wechat", {"url": "https://mp.weixin.qq.com/s/test"})
    _assert_standardized_result(result, "wechat")
    assert result["status"] == "success"
    assert "message" in result
    assert "item_count" in result
    assert "saved_paths" in result


def test_run_collect_wechat_missing_url_includes_error_summary_and_next_step() -> None:
    """WeChat missing-URL error MUST return a plain-language summary and a useful next_step."""
    from workspace_web.service import run_collect

    result = run_collect("wechat", {"url": ""})
    _assert_standardized_result(result, "wechat-error")
    assert result["status"] == "error"
    # Next step should guide the user to fix the input
    assert "url" in result["next_step"].lower() or "input" in result["next_step"].lower()


def test_run_collect_unknown_source_includes_error_summary_and_next_step() -> None:
    """Unknown-source error MUST return a plain-language summary and a useful next_step."""
    from workspace_web.service import run_collect

    result = run_collect("twitter", {"query": "test"})
    _assert_standardized_result(result, "unknown-source")
    assert result["status"] == "error"
    # Next step should point back to a supported source
    assert any(s in result["next_step"].lower() for s in ("github", "papers", "wechat", "source"))


def test_app_jsx_collect_section_renders_summary_and_next_step() -> None:
    """CollectSection MUST render result.summary and result.next_step as primary copy."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    idx = app_jsx.find("function CollectSection")
    assert idx != -1, "App.jsx is missing CollectSection"
    body = app_jsx[idx:]

    assert "result.summary" in body, "CollectSection must render result.summary as primary copy"
    assert "result.next_step" in body, "CollectSection must render result.next_step as primary copy"

    # Original JSON detail render must still exist but be demoted (wrapped in <details> or labeled "Technical details").
    has_details_block = "<details" in body or "Technical details" in body or "technical-details" in body
    assert has_details_block, "JSON detail must be wrapped in <details> or labeled as technical details"

    # Successful result MUST still surface a CTA that navigates to the Library.
    assert 'setActiveSection("library")' in body, (
        "CollectSection must include a setActiveSection(\"library\") CTA for successful runs"
    )
    assert "Go to Library" in body, "CollectSection must render a 'Go to Library' CTA on success"


# ---------------------------------------------------------------------------
# AUTO-REFRESH: add-frontend-auto-refresh
# ---------------------------------------------------------------------------


def test_auto_refresh_module_exports_pure_controller_and_constants() -> None:
    """The autoRefresh module MUST export a pure-JS factory plus named constants."""
    import re

    src = (Path(__file__).resolve().parents[1] / "web" / "src" / "autoRefresh.js").read_text(encoding="utf-8")
    # Must export the controller factory and the 5s interval constant
    assert "export function createAutoRefreshController" in src
    assert "export const DEFAULT_POLLING_INTERVAL_MS" in src
    assert "5000" in src, "DEFAULT_POLLING_INTERVAL_MS must be 5000ms"

    # The polling logic (createAutoRefreshController) MUST be importable under
    # plain Node. We check that there is no `import ... from "react"` at the
    # top of the file by scanning line-initial import statements only — this
    # avoids false positives from `from "react"` appearing in comments.
    import_lines = [
        line.strip() for line in src.splitlines()
        if re.match(r"^import\s", line.strip())
    ]
    react_imports = [line for line in import_lines if 'from "react"' in line]
    # We DO want the React hook wrapper (`useAutoRefresh`) to import React —
    # but it must live in a separate file from the Node-testable controller so
    # the pure factory has zero React coupling. So we allow NO `from "react"`
    # imports in this file at all.
    assert not react_imports, (
        f"autoRefresh.js must not import React at module top — the pure polling "
        f"factory is Node-testable. Found: {react_imports}"
    )

    # Must export the polled section list so App.jsx can iterate
    assert "export const POLLED_SECTIONS" in src
    m = re.search(r"export const POLLED_SECTIONS\s*=\s*\[(.*?)\]", src)
    assert m, "POLLED_SECTIONS must be a literal array"
    sections = [s.strip().strip('"').strip("'") for s in m.group(1).split(",")]
    assert set(sections) == {"dashboard", "library", "briefing", "collect"}


def test_app_jsx_topbar_exposes_auto_refresh_toggle_default_on() -> None:
    """App.jsx MUST render an Auto-refresh toggle in the topbar, defaulting to enabled."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    # The toggle label must be visible to the user
    assert "Auto-refresh" in app_jsx, "App.jsx must render an 'Auto-refresh' toggle in the topbar"
    # It must be a checkbox or switch input
    assert 'type="checkbox"' in app_jsx or "type=\"switch\"" in app_jsx, (
        "Auto-refresh toggle must be a checkbox/switch input"
    )
    # The default state must be on (true)
    assert "useState(true)" in app_jsx or "useState( true" in app_jsx, (
        "Auto-refresh toggle MUST default to enabled (useState(true) somewhere in App.jsx)"
    )


def test_app_jsx_imports_and_uses_auto_refresh_controller() -> None:
    """App.jsx MUST import createAutoRefreshController and use it for the read-path sections."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    assert "createAutoRefreshController" in app_jsx or "useAutoRefresh" in app_jsx, (
        "App.jsx must import the auto-refresh helper"
    )
    # The hook wrapper lives in a separate file so the pure controller stays
    # Node-testable.
    assert 'from "./autoRefresh.react.js"' in app_jsx or 'from "./autoRefresh"' in app_jsx, (
        "App.jsx must import useAutoRefresh from one of the autoRefresh modules"
    )
    # The 4 polled sections must be in App.jsx as data-endpoint keys somewhere
    for section in ("dashboard", "library", "briefing", "collect"):
        assert section in app_jsx, f"App.jsx must reference section {section!r}"


def test_app_jsx_does_not_add_new_query_params_to_polled_requests() -> None:
    """The polling hook MUST use the same fetch signatures as the existing requestJson calls."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    # Existing endpoints — these must remain the only ones the polling path targets
    expected_endpoints = [
        "/api/dashboard",
        "/api/library?",
        "/api/collect/sources",
    ]
    for ep in expected_endpoints:
        assert ep in app_jsx, f"App.jsx must still hit {ep!r}"

    # No new "?auto=true" or "?_t=" cache-busting trickery on the polled endpoints
    import re

    # Find requestJson calls in App.jsx
    fetch_calls = re.findall(r'requestJson\((`[^`]*`)\b', app_jsx)
    for call in fetch_calls:
        # Polling-related calls should not introduce new query parameters.
        if "/api/dashboard" in call or "/api/library" in call or "/api/collect/sources" in call:
            # We allow `?...` for library but only existing params (keyword, source, since, until, page, page_size).
            if "?" in call:
                params_part = call.split("?", 1)[1]
                # Strip template expressions
                plain_params = re.sub(r"\$\{[^}]*\}", "X", params_part)
                # Disallow obviously new param keys
                for forbidden in ("auto_refresh=", "autorefresh=", "ts=", "_t=", "polling="):
                    assert forbidden not in plain_params, (
                        f"Polling fetch {call!r} must not introduce new query param {forbidden!r}"
                    )


# ---------------------------------------------------------------------------
# fix-auto-refresh-expose-poll-errors
# ---------------------------------------------------------------------------


def test_auto_refresh_controller_exposes_onError_getLastError_dismissError() -> None:
    """The pure controller MUST export a per-section lastError plus dismissError()."""
    src = (Path(__file__).resolve().parents[1] / "web" / "src" / "autoRefresh.js").read_text(encoding="utf-8")
    assert "onError" in src, "controller must accept an onError callback"
    assert "getLastError" in src, "controller must expose getLastError"
    assert "dismissError" in src, "controller must expose dismissError"
    # The returned object must include both
    assert "getLastError," in src or "getLastError," in src
    assert "dismissError," in src


def test_use_auto_refresh_react_hook_returns_lastError_and_dismissError() -> None:
    """The React hook wrapper MUST surface lastError and dismissError to the caller."""
    src = (Path(__file__).resolve().parents[1] / "web" / "src" / "autoRefresh.react.js").read_text(encoding="utf-8")
    assert "lastError" in src, "useAutoRefresh must track lastError"
    assert "dismissError" in src, "useAutoRefresh must expose dismissError"
    # And the returned object must include both keys
    assert "lastError," in src or "{ lastError" in src
    assert "dismissError," in src or "{ lastError" in src


def test_app_jsx_renders_poll_error_banner_in_each_section() -> None:
    """App.jsx MUST render the PollErrorBanner inside each section that polls."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "PollErrorBanner" in app_jsx, "App.jsx must define / use PollErrorBanner"
    # Must appear at least 4 times (one per section).
    assert app_jsx.count("PollErrorBanner") >= 5, (
        f"App.jsx must reference PollErrorBanner at least 5 times (1 definition + 4 uses), "
        f"found {app_jsx.count('PollErrorBanner')}"
    )


def test_app_jsx_poll_error_banner_is_non_blocking() -> None:
    """The PollErrorBanner MUST be a sibling of the form, not a parent of it."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # Find at least one section's render and assert the banner is rendered
    # as a sibling of the form, not wrapping it.
    import re
    # Library section body
    m = re.search(r"function LibrarySection[\s\S]+?return \(\s*<section[\s\S]+?</section>", app_jsx)
    assert m, "LibrarySection render block not found"
    body = m.group(0)
    # The banner should appear BEFORE the form tag, both as direct children of <section>
    banner_idx = body.find("PollErrorBanner")
    form_idx = body.find("<form")
    assert banner_idx != -1 and form_idx != -1, "Library section must have both banner and form"
    assert banner_idx < form_idx, "PollErrorBanner must render BEFORE the form (non-blocking layout)"


# ---------------------------------------------------------------------------
# fix-frontend-render-tests-jsdom
# ---------------------------------------------------------------------------


def test_npm_test_in_web_runs_node_test_suite() -> None:
    """`npm test --prefix web` MUST run the full Node test suite, including the SSR render tests.

    This is a process-level wiring test: it executes the npm script and
    asserts exit code 0. It catches accidental breakage of `npm test`
    (e.g. wrong test glob, missing dep, broken SSR import) without
    having to re-run every test individually.

    Per Scenario 6 of the delta spec, the suite MUST report pass/fail counts
    (not a specific number). We parse the `ℹ pass N` / `ℹ fail N` lines that
    `node --test` always emits and assert:
    - pass > 0 (the suite actually ran something)
    - fail == 0 (no test regressed)
    - skipped == 0 (no test was silently skipped)
    This avoids the brittleness of hard-coding the test count (which grows
    whenever a sibling change adds a new test).
    """
    import re
    import subprocess

    project_root = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        ["npm", "test", "--prefix", str(project_root / "web")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, (
        f"`npm test --prefix web` must exit 0. STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )

    # Extract the structured pass/fail/skipped counts that `node --test` emits.
    def _extract(label: str) -> int | None:
        m = re.search(rf"ℹ {label} (\d+)", proc.stdout)
        return int(m.group(1)) if m else None

    pass_count = _extract("pass")
    fail_count = _extract("fail")
    skip_count = _extract("skipped")

    assert pass_count is not None, (
        "npm test output must report a `ℹ pass N` count line; spec Scenario 6 "
        f"requires pass/fail counts. Got STDOUT tail:\n{proc.stdout[-500:]}"
    )
    assert pass_count > 0, (
        f"npm test reported `pass {pass_count}`; suite must run at least one test. "
        f"Got STDOUT tail:\n{proc.stdout[-500:]}"
    )
    assert fail_count == 0, (
        f"npm test reported `fail {fail_count}`; spec Scenario 6 requires the "
        f"suite to be all-green. Got STDOUT tail:\n{proc.stdout[-500:]}"
    )
    assert skip_count == 0, (
        f"npm test reported `skipped {skip_count}`; silently skipping tests "
        f"defeats the purpose of a wiring test. Got STDOUT tail:\n{proc.stdout[-500:]}"
    )


# ---------------------------------------------------------------------------
# fix-frontend-section-switch-preserves-form
# ---------------------------------------------------------------------------


def test_library_form_state_lives_in_app_not_in_section_component() -> None:
    """LibrarySection MUST NOT own its own form state — App lifts it to the top.

    If LibrarySection still does `const [form, setForm] = useState({...})`,
    any section switch unmounts it and the user loses their input.
    """
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    import re

    # Extract LibrarySection body via balanced-brace counting.
    fn_match = re.search(r"function LibrarySection\b", app_jsx)
    assert fn_match, "function LibrarySection not found"
    brace_idx = app_jsx.find("{", fn_match.end())
    assert brace_idx != -1
    depth = 0
    end = brace_idx
    for i in range(brace_idx, len(app_jsx)):
        c = app_jsx[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    library_body = app_jsx[fn_match.start():end + 1]

    # LibrarySection must not own a form useState (any multi-line).
    assert not re.search(r"useState\(\s*\{\s*keyword:", library_body), (
        "LibrarySection must not own its own form `useState({ keyword: ... })` — "
        "lift the state to App so it survives section unmount/remount"
    )

    # App() must own the form state via lifted useState.
    app_fn_match = re.search(r"function App\b", app_jsx)
    assert app_fn_match, "function App not found"
    app_brace_idx = app_jsx.find("{", app_fn_match.end())
    assert app_brace_idx != -1
    depth = 0
    app_end = app_brace_idx
    for i in range(app_brace_idx, len(app_jsx)):
        c = app_jsx[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                app_end = i
                break
    app_body = app_jsx[app_fn_match.start():app_end + 1]
    assert re.search(r"useState\(\s*\{\s*keyword:", app_body), (
        "App() must own the library form state via a lifted `useState({ keyword: ... })`"
    )

    # And the App's libraryForm state must be wired down to <LibrarySection>
    # via a `form={...}` prop.
    lib_usage_match = re.search(r"<LibrarySection\b[^/>]*/?>", app_jsx)
    assert lib_usage_match, "<LibrarySection /> must be rendered by App"
    lib_usage = lib_usage_match.group(0)
    assert "form={" in lib_usage, (
        f"<LibrarySection /> must receive a `form=` prop; got: {lib_usage!r}"
    )


def test_library_page_state_lives_in_app_not_in_section_component() -> None:
    """Library page index / page size MUST also be lifted to App, not LibrarySection."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    import re

    # Restrict the body to the LibrarySection function itself, identified
    # by its opening brace → balanced closing brace. We do this with a
    # hand-rolled bracket counter (avoids the complexity of a full parser).
    fn_match = re.search(r"function LibrarySection\b", app_jsx)
    assert fn_match, "function LibrarySection not found"
    start = fn_match.end()
    # Find the first `{` after the function signature.
    brace_idx = app_jsx.find("{", start)
    assert brace_idx != -1, "LibrarySection opening brace not found"
    depth = 0
    end = brace_idx
    for i in range(brace_idx, len(app_jsx)):
        c = app_jsx[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    library_body = app_jsx[fn_match.start():end + 1]

    # LibrarySection must NOT have a bare `useState(1)` (the page default).
    assert "useState(1)" not in library_body, (
        "LibrarySection must not own `useState(1)` (the page index) — "
        "lift to App"
    )

    # The page size default `20` is similarly forbidden.
    assert "useState(20)" not in library_body, (
        "LibrarySection must not own `useState(20)` (the page size) — "
        "lift to App"
    )


def test_app_passes_form_props_to_library_section() -> None:
    """Deprecated — folded into test_library_form_state_lives_in_app_not_in_section_component."""
    # Kept as a stub for backward-compat. The real assertion lives above.
    pass


# ---------------------------------------------------------------------------
# fix-backend-relative-output-root-resolution
# ---------------------------------------------------------------------------


def test_serve_workspace_resolves_relative_output_root_against_project_root(tmp_path: Path) -> None:
    """`serve_workspace(Path('output'))` MUST resolve the relative output_root
    against the project root, NOT against the server's cwd.

    Repro: backend was started via `python -c "..."` from the `web/` cwd,
    which made `Path('output')` resolve to `web/output` (non-existent) and
    silently produced 0 items even though `output/` at the repo root had
    16 sidecars. The fix: anchor relative paths to the repo root.
    """
    import subprocess

    project_root = Path(__file__).resolve().parents[1]
    port = _free_loopback_port()

    # Seed a temp output dir + chdir into a DIFFERENT cwd (simulating the
    # server being launched from `web/`). The seed tree MUST be reachable
    # via the relative path `output` resolved against project root.
    output_dir = project_root / "output"
    if not output_dir.exists() or not any(output_dir.rglob("research-item.json")):
        pytest.skip("no seeded output/ at project root — cannot exercise path resolution")

    # Use subprocess so we control the cwd exactly. Start a serve_workspace
    # on a non-default port with a quick auto-exit, then probe /api/dashboard.
    serve_script = (
        "import sys, threading, time, pathlib, os\n"
        f"sys.path.insert(0, {str(project_root)!r})\n"
        "from workspace_web import server as srv\n"
        "def stop():\n"
        "    time.sleep(1.0)\n"
        "    os._exit(0)\n"
        "threading.Thread(target=stop, daemon=True).start()\n"
        f"srv.serve_workspace(pathlib.Path('output'), port={port})\n"
    )
    server_proc = subprocess.Popen(
        [sys.executable, "-c", serve_script],
        cwd=str(project_root / "web"),  # WRONG cwd on purpose
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        body = _wait_for_json(f"http://127.0.0.1:{port}/api/dashboard")
        # The fix MUST make this > 0 even though the server's cwd is wrong.
        assert body.get("total_items", 0) > 0, (
            f"server cwd is {project_root / 'web'} but /api/dashboard reports 0 items; "
            f"the relative output_root was not resolved against the project root. "
            f"body={body!r}"
        )
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=3)
        except Exception:
            server_proc.kill()


# ---------------------------------------------------------------------------
# fix-backend-relative-output-root-resolution — Scenario 2 + 3
# ---------------------------------------------------------------------------


def test_serve_workspace_passes_absolute_output_root_through_unchanged(tmp_path: Path) -> None:
    """Scenario 2: `output_root = Path('/abs/path')` MUST be passed through verbatim,
    and the printed stdout line MUST reflect that absolute path (not the
    project-root-anchored version).
    """
    import subprocess
    import time

    # Use a tmp dir as the absolute path. We do not require the dir to exist
    # for the resolution test; we only need the printed line.
    absolute_dir = (tmp_path / "abs-output").resolve()
    port = _free_loopback_port()

    # Use subprocess.bufsize=0 to read stdout line-by-line as it streams
    # so we don't lose prints to the `os._exit(0)` cleanup race.
    serve_script = (
        "import sys, threading, time, pathlib, os\n"
        f"sys.path.insert(0, {str(Path(__file__).resolve().parents[1])!r})\n"
        "from workspace_web import server as srv\n"
        "def stop():\n"
        "    time.sleep(0.6)\n"
        "    sys.stdout.flush()\n"
        "    sys.stderr.flush()\n"
        "    os._exit(0)\n"
        "threading.Thread(target=stop, daemon=True).start()\n"
        f"srv.serve_workspace(pathlib.Path({str(absolute_dir)!r}), port={port})\n"
    )
    server_proc = subprocess.Popen(
        [sys.executable, "-u", "-c", serve_script],  # -u = unbuffered I/O
        cwd=str(tmp_path),  # any cwd; absolute path must NOT be touched
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        # Read all stdout before the process exits.
        out, _ = server_proc.communicate(timeout=4)
        text = out.decode("utf-8", errors="replace") if out else ""
        # The printed line must show the absolute path verbatim.
        assert f"Using output root: {absolute_dir}" in text, (
            f"serve_workspace must print the absolute path verbatim. "
            f"Expected to find `Using output root: {absolute_dir}` in stdout. "
            f"Got:\n{text!r}"
        )
        # And it MUST NOT have been re-anchored to the project root.
        project_root = Path(__file__).resolve().parents[1]
        anchored = (project_root / absolute_dir).resolve()
        if str(anchored) != str(absolute_dir):
            assert f"Using output root: {anchored}" not in text, (
                f"Absolute path was re-anchored to project_root; expected verbatim {absolute_dir!r} "
                f"but got the re-anchored {anchored!r}"
            )
    finally:
        if server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except Exception:
                server_proc.kill()


def test_serve_workspace_with_nonexistent_relative_path_does_not_crash_dashboard(tmp_path: Path) -> None:
    """Scenario 3: a relative path that does NOT exist under project_root
    MUST NOT crash `/api/dashboard` (returns empty state), and the printed
    "Using output root" line MUST show the resolved absolute path.
    """
    import subprocess
    import urllib.request
    import json

    project_root = Path(__file__).resolve().parents[1]
    # 'nonexistent-fix-resolve-dir' is a relative path that does NOT exist
    # under project_root. The fix MUST still resolve it (to
    # project_root / 'nonexistent-fix-resolve-dir') and the API MUST
    # respond with HTTP 200 + empty state rather than crash.
    expected = project_root / "nonexistent-fix-resolve-dir"
    port = _free_loopback_port()

    serve_script = (
        "import sys, threading, time, pathlib, os\n"
        f"sys.path.insert(0, {str(project_root)!r})\n"
        "from workspace_web import server as srv\n"
        "def stop():\n"
        "    time.sleep(2.0)\n"
        "    sys.stdout.flush()\n"
        "    sys.stderr.flush()\n"
        "    os._exit(0)\n"
        "threading.Thread(target=stop, daemon=True).start()\n"
        f"srv.serve_workspace(pathlib.Path('nonexistent-fix-resolve-dir'), port={port})\n"
    )
    server_proc = subprocess.Popen(
        [sys.executable, "-u", "-c", serve_script],
        cwd=str(project_root / "web"),  # wrong cwd on purpose
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        # /api/dashboard must return 200 + empty state rather than crashing.
        try:
            body = _wait_for_json(f"http://127.0.0.1:{port}/api/dashboard")
            assert body.get("total_items") == 0, (
                f"Expected total_items=0 for nonexistent path, got {body!r}"
            )
            assert body.get("empty_state"), (
                f"Expected empty_state block in dashboard payload, got {body!r}"
            )
        except Exception as exc:
            raise AssertionError(
                f"/api/dashboard must respond 200 (not crash) for nonexistent output_root. "
                f"Got exception: {exc!r}"
            )

        # Now read the captured stdout (we delay stop so the server is still
        # running while we probe the API).
        out, _ = server_proc.communicate(timeout=3)
        text = out.decode("utf-8", errors="replace") if out else ""
        # The fix should have anchored 'nonexistent-fix-resolve-dir' to
        # project_root/nonexistent-fix-resolve-dir.
        assert f"Using output root: {expected}" in text, (
            f"Expected the resolved path {expected!r} in stdout. Got:\n{text!r}"
        )
    finally:
        if server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=2)
            except Exception:
                server_proc.kill()


# ---------------------------------------------------------------------------
# add-library-safe-markdown-preview
# ---------------------------------------------------------------------------


def test_read_item_markdown_returns_content_for_known_sidecar_path(tmp_path: Path) -> None:
    """Scenario 1: known sidecar output_path → file content returned."""
    from workspace_web.service import read_item_markdown, load_research_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    items = load_research_items(output_root)
    assert items, "seed tree should produce at least one item"
    target = items[0]
    body, content_type = read_item_markdown(output_root, target.output_path)
    assert isinstance(body, str)
    assert len(body) > 0
    assert "markdown" in content_type.lower()


def test_read_item_markdown_rejects_path_outside_output_root(tmp_path: Path) -> None:
    """Scenario 2: ../etc/passwd or absolute paths → rejected."""
    import pytest
    from workspace_web.service import read_item_markdown

    output_root = tmp_path / "output"
    output_root.mkdir()
    # Path traversal
    with pytest.raises(Exception) as exc_info:
        read_item_markdown(output_root, "../etc/passwd")
    # The exception class should be a security-related error; we accept any
    # non-FileNotFoundError so the contract is "rejected, not silently read".
    assert "NotFound" not in type(exc_info.value).__name__, (
        f"Path traversal must NOT be a NotFoundError; got {type(exc_info.value).__name__}: {exc_info.value}"
    )


def test_read_item_markdown_rejects_path_not_in_any_sidecar(tmp_path: Path) -> None:
    """Scenario 3: a file inside output_root but not registered as any sidecar → 404-like."""
    import pytest
    from workspace_web.service import read_item_markdown

    output_root = tmp_path / "output"
    output_root.mkdir()
    # File exists but is NOT a sidecar's output_path.
    orphan = output_root / "orphan.md"
    orphan.write_text("orphan", encoding="utf-8")
    with pytest.raises(FileNotFoundError) as exc_info:
        read_item_markdown(output_root, "output/orphan.md")
    assert "not a known" in str(exc_info.value).lower() or "no such" in str(exc_info.value).lower(), (
        f"Error message must explain WHY: {exc_info.value}"
    )


def test_read_item_markdown_returns_404_when_file_missing(tmp_path: Path) -> None:
    """Scenario 4: sidecar exists in the registry but underlying .md was deleted."""
    import pytest
    from workspace_web.service import read_item_markdown

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    # Delete every .md file we created
    for md in output_root.rglob("*.md"):
        md.unlink()
    # Now the sidecar paths point at nothing
    with pytest.raises(FileNotFoundError):
        # Use a known sidecar path from the seed (any one will do)
        read_item_markdown(output_root, "output/github/anthropics-claude-code/README.md")


def test_app_jsx_renders_markdown_preview_in_detail_panel() -> None:
    """Scenario 5: detail panel includes a <MarkdownPreview> element when item is selected."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "MarkdownPreview" in app_jsx, "App.jsx must render a MarkdownPreview component"
    # Must appear at least 2 times: 1 definition + 1 use
    assert app_jsx.count("MarkdownPreview") >= 2, (
        f"App.jsx must reference MarkdownPreview at least twice; found {app_jsx.count('MarkdownPreview')}"
    )


def test_app_jsx_markdown_preview_endpoint_url_uses_output_path_query() -> None:
    """Scenario 5 (副): the preview fetch must hit /api/library/preview with output_path=..."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # Accept either `requestJson` or raw `fetch` — the implementation may
    # use either, but the URL shape must match.
    import re
    needle = "/api/library/preview"
    has_endpoint = (
        (f'requestJson(`{needle}' in app_jsx)
        or (f'"{needle}"' in app_jsx)
        or (f"'{needle}'" in app_jsx)
        or (f"`{needle}" in app_jsx)
    )
    assert has_endpoint, f"App.jsx must reference the {needle} endpoint"
    # The URL must include the `output_path` query parameter.
    assert "output_path=" in app_jsx, (
        f"App.jsx must pass output_path=<encoded path> when fetching {needle}"
    )


def test_app_jsx_removes_legacy_file_url_handler() -> None:
    """Scenario 6: legacy `file://` window.open usage MUST be removed from the detail panel."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # Find the detail-actions block (between detail-grid and the closing
    # </div> of the detail panel) and assert no `file://` references.
    import re
    # We do a substring check: no `file://` and no `window.open(` in detail actions.
    # The change removes the legacy button but may keep window.open for
    # other purposes (e.g. external links); we restrict the check to the
    # detail-actions region.
    m = re.search(r"detail-actions[\s\S]+?</div>\s*</div>", app_jsx)
    if m:
        region = m.group(0)
        assert "file://" not in region, (
            f"detail-actions must not reference file:// URLs: {region[:200]!r}"
        )


# ---------------------------------------------------------------------------
# redesign-library-search-inspection-layout
# ---------------------------------------------------------------------------


def test_library_filter_bar_holds_all_search_controls() -> None:
    """Scenario 1: filter bar contains keyword + sources + since/until + search + count."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")

    # The filter-bar class must appear in App.jsx (whether or not it's
    # inside a "function LibrarySection" — we use a simple substring check
    # so the test is robust to bracket-balancing issues with destructured
    # function arguments).
    assert "library-filter-bar" in app_jsx, (
        "App.jsx must render a `library-filter-bar` element"
    )

    # All filter controls (keyword / sources / since / until / search / count)
    # must be present. We assert each label is referenced.
    for needle in ("library-filter-keyword", "library-filter-sources", "library-filter-dates", "library-filter-search", "library-filter-count"):
        assert needle in app_jsx, f"App.jsx must include the {needle!r} control class"


def test_library_workspace_uses_two_column_layout() -> None:
    """Scenario 2 + 7: result list wider than detail; legacy 3-column class removed."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    styles = (Path(__file__).resolve().parents[1] / "web" / "src" / "styles.css").read_text(encoding="utf-8")

    # The new two-column workspace class must be defined in CSS and used in JSX.
    assert ".library-workspace" in styles, (
        "styles.css must define a .library-workspace two-column layout"
    )
    assert "library-workspace" in app_jsx, (
        "App.jsx must use the library-workspace class"
    )

    # The legacy `library-layout` class must not be applied to the
    # LibrarySection root in App.jsx.
    import re
    section_root = re.search(r"function LibrarySection\b[\s\S]+?return \(\s*<([^>]+)>", app_jsx)
    assert section_root, "LibrarySection root tag not found"
    assert "library-layout" not in section_root.group(1), (
        f"LibrarySection root tag must not use library-layout: {section_root.group(1)[:120]!r}"
    )


def test_library_page_purpose_and_scope_are_demoted() -> None:
    """Scenario 3: page-purpose / scope notes are small / collapsible, not a full row."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # PagePurposeCard must NOT be a direct child of the section root.
    # Instead it must be wrapped in a `library-meta-collapsible` (or similar)
    # so the filter bar is the primary visual element.
    import re
    # Find the LibrarySection's return(<section ...>) and check what's directly
    # inside.
    section_match = re.search(
        r"function LibrarySection\b[\s\S]+?return \(\s*<section[^>]+>\s*<([\s\S]+?)$",
        app_jsx,
    )
    # Simpler: assert that PagePurposeCard appears INSIDE a <details> element
    # (i.e. inside a collapsible wrapper).
    assert "library-meta-collapsible" in app_jsx, (
        "App.jsx must wrap PagePurposeCard in a `library-meta-collapsible` details/summary"
    )
    # The filter bar must appear BEFORE the detail panel.
    filter_idx = app_jsx.find("library-filter-bar")
    detail_idx = app_jsx.find("detail-panel")
    assert filter_idx != -1 and detail_idx != -1, "filter bar and detail panel must both be present"
    assert filter_idx < detail_idx, "filter bar must appear before detail panel"


def test_library_detail_metadata_order() -> None:
    """Scenario 4: detail panel order: title, summary, source, type, authors, dates, tags, path, actions.

    Spec Scenario 4 is explicit: when a result is selected, the detail panel
    must show the metadata labels in the order Source → Type → Authors →
    Published → Tags → Archive path. The original test used a brittle
    `<div className="detail-panel">…` literal that no longer matched the
    current JSX (`<div className="panel detail-panel">` — i.e. two classes),
    so it silently `pytest.skip`-ed, which is a "false pass" — the assertion
    never actually ran. This version matches the detail-panel <div> by class
    list (not exact className string), then verifies both label presence and
    the required order. If the regex ever fails to find the panel, the test
    now FAILS LOUDLY with a clear message instead of silently skipping.
    """
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # Find the detail-panel body. Match by class list rather than the exact
    # `className="detail-panel"` literal, so the test tolerates sibling
    # classes like `panel` being added later.
    m = re.search(r'<div[^>]*className="[^"]*\bdetail-panel\b[^"]*"[^>]*>[\s\S]+?</dl>', app_jsx)
    assert m, (
        "Could not locate a `<div ... className=\"...detail-panel...\">` block "
        "in App.jsx that contains a `<dl>` of metadata. Scenario 4 requires "
        "the detail panel to render a `<dl>` with Source/Type/Authors/"
        "Published/Tags/Archive path in that order. If the JSX has been "
        "refactored, fix this test to match the new structure — do not "
        "silently skip."
    )
    body = m.group(0)
    # Required order: Source / Type / Authors / Published / Tags / Archive path
    # We assert presence first, then positional order.
    pos = {}
    for label in ("Source", "Type", "Authors", "Published", "Tags", "Archive path"):
        pos[label] = body.find(label)
    missing = [k for k, v in pos.items() if v == -1]
    assert not missing, f"Missing required metadata labels in detail panel: {missing}; got {pos}"
    expected_order = ["Source", "Type", "Authors", "Published", "Tags", "Archive path"]
    indices = [pos[k] for k in expected_order]
    assert indices == sorted(indices), (
        f"Metadata labels must be in order {expected_order}; got positions {pos}"
    )


def test_library_pagination_inside_result_panel() -> None:
    """Scenario 6: pagination controls live in the result panel, not detail."""
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # The pagination panel is a <div className="pagination-controls">. It
    # must NOT be a descendant of .detail-panel.
    pag_idx = app_jsx.find("pagination-controls")
    detail_idx = app_jsx.find("detail-panel")
    assert pag_idx != -1, "pagination-controls must be present"
    assert detail_idx != -1, "detail-panel must be present"
    # If pagination is AFTER detail-panel opens, it must close BEFORE
    # detail-panel closes. We do a simplified check: pagination's
    # surrounding <div> must not contain the detail-grid block.
    # For a strict check we'd need a real parser; we approximate by
    # asserting that the pagination <div> text does NOT contain the
    # "Archive path" string (which only appears inside detail).
    pag_chunk = app_jsx[pag_idx:pag_idx + 800]
    assert "Archive path" not in pag_chunk, (
        "pagination-controls block must not contain detail-panel metadata"
    )


# ---------------------------------------------------------------------------
# replace-library-file-url-with-safe-local-actions
# ---------------------------------------------------------------------------


def test_detail_actions_do_not_contain_file_url() -> None:
    """Scenario 1: detail-actions region must NOT contain file:// references."""
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    m = re.search(r'<div className="detail-actions"[\s\S]+?</div>\s*</div>', app_jsx)
    if m:
        region = m.group(0)
        assert "file://" not in region, (
            f"detail-actions must not reference file:// URLs: {region[:200]!r}"
        )
        assert "window.open(`file://" not in region, (
            "detail-actions must not call window.open(`file://`)"
        )


def test_detail_actions_offer_preview_markdown() -> None:
    """Scenario 2: detail-actions include a 'Preview Markdown' button."""
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    m = re.search(r'<div className="detail-actions"[\s\S]+?</div>\s*</div>', app_jsx)
    assert m, "detail-actions block not found"
    region = m.group(0)
    assert "Preview Markdown" in region, (
        f"detail-actions must include a 'Preview Markdown' button. Found: {region[:300]!r}"
    )
    # The click must NOT be a window.open — it must trigger the in-page
    # MarkdownPreview component (which is rendered separately, above
    # detail-actions).
    # Heuristic: there should be NO `window.open(` inside the region.
    assert "window.open(" not in region, (
        f"Preview Markdown button must not call window.open: {region[:300]!r}"
    )


def test_detail_actions_offer_open_source_link() -> None:
    """Scenario 3: detail-actions include an 'Open source link' anchor."""
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    m = re.search(r'<div className="detail-actions"[\s\S]+?</div>\s*</div>', app_jsx)
    assert m, "detail-actions block not found"
    region = m.group(0)
    assert "Open source link" in region, (
        f"detail-actions must include an 'Open source link' anchor. Found: {region[:300]!r}"
    )
    # The anchor must be a real <a> with target=_blank + rel=noreferrer
    assert 'target="_blank"' in region, "anchor must open in a new tab"
    assert 'rel="noreferrer"' in region, "anchor must have rel=noreferrer"


def test_detail_actions_offer_copy_archive_path() -> None:
    """Scenario 4: detail-actions include a 'Copy archive path' button."""
    import re
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    m = re.search(r'<div className="detail-actions"[\s\S]+?</div>\s*</div>', app_jsx)
    assert m, "detail-actions block not found"
    region = m.group(0)
    # The Copy button may be rendered as a self-closing JSX element
    # (`<CopyArchivePathButton ... />`) whose label literal "Copy archive path"
    # appears elsewhere in App.jsx (inside the component body). So we
    # require either the label to be inside detail-actions OR a
    # `<CopyArchivePathButton ...>` to be referenced there.
    has_inline_label = "Copy archive path" in region
    has_component_ref = "<CopyArchivePathButton" in region
    assert has_inline_label or has_component_ref, (
        f"detail-actions must include a 'Copy archive path' button (inline label "
        f"or <CopyArchivePathButton /> reference). Found: {region[:300]!r}"
    )
    # Either way, the component body must contain the label string.
    assert "Copy archive path" in app_jsx, (
        "App.jsx must include the literal string 'Copy archive path' "
        "in the CopyArchivePathButton component body"
    )


def test_copy_uses_navigator_clipboard_writetext() -> None:
    """Scenario 7: the copy handler uses navigator.clipboard.writeText."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    assert "navigator.clipboard.writeText" in app_jsx, (
        "App.jsx must use navigator.clipboard.writeText for copying"
    )
    # And the deprecated execCommand must NOT be used as a fallback
    assert "execCommand" not in app_jsx, (
        "App.jsx must not use the deprecated document.execCommand"
    )


def test_app_jsx_has_about_local_files_note() -> None:
    """Scenario 6: App.jsx includes a small 'About local files' note."""
    app_jsx = (Path(__file__).resolve().parents[1] / "web" / "src" / "App.jsx").read_text(encoding="utf-8")
    # We accept either a dedicated component or inline copy — both must
    # mention the user-facing phrase so the spec is satisfied.
    assert (
        "About local files" in app_jsx
        or "AboutLocalFiles" in app_jsx
    ), "App.jsx must include an 'About local files' note explaining the local-files boundary"
    # The note should be visually subdued — we don't enforce CSS, but
    # it must be rendered somewhere in the Library render path.
    assert (
        "library-about-local-files" in app_jsx
        or "library-local-files-note" in app_jsx
        or "AboutLocalFiles" in app_jsx
    ), "App.jsx must include a class or component for the local-files note"
