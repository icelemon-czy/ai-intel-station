from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ai_intel_station.library.items import ResearchItem
from ai_intel_station.briefing.markdown import write_markdown


_WEB_WORKSPACE_SOURCE_FILES = (
    "workspaceShared.jsx",
    "DashboardSection.jsx",
    "LibrarySection.jsx",
    "BriefingSection.jsx",
    "CollectSection.jsx",
    "App.jsx",
)


def _read_web_workspace_source() -> str:
    source_root = Path(__file__).resolve().parents[1] / "frontend" / "src"
    return "\n".join(
        (source_root / name).read_text(encoding="utf-8")
        for name in _WEB_WORKSPACE_SOURCE_FILES
    )


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
    from ai_intel_station.adapters.web.service import workspace_sections

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
    from ai_intel_station.adapters.web.service import workspace_sections

    sections = workspace_sections()
    section_ids = [s["id"] for s in sections]

    assert "collect" in section_ids, f"Expected 'collect' in section ids: {section_ids}"
    collect_section = next(s for s in sections if s["id"] == "collect")
    assert collect_section["label"] == "Collect Workspace"


def test_collect_workspace_has_description() -> None:
    """Test that Collect Workspace section includes description for page heading."""
    from ai_intel_station.adapters.web.service import workspace_sections

    sections = workspace_sections()
    collect_section = next(s for s in sections if s["id"] == "collect")
    assert "description" in collect_section, "Collect section should have description for page heading"
    assert len(collect_section["description"]) > 0


def test_list_collect_sources_returns_all_supported_sources() -> None:
    """Test that collect workspace lists all supported sources."""
    from ai_intel_station.adapters.web.service import list_collect_sources

    sources = list_collect_sources()
    source_ids = [s["id"] for s in sources]

    assert "github" in source_ids
    assert "papers" in source_ids
    assert "wechat" in source_ids


def test_get_collect_form_returns_source_specific_fields() -> None:
    """Test that collect form returns fields specific to each source."""
    from ai_intel_station.adapters.web.service import get_collect_form

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
    from ai_intel_station.adapters.web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)
    _seed_briefings(output_root)

    overview = build_dashboard_overview(output_root)

    assert overview["total_items"] == 4
    assert overview["source_counts"] == {"github": 2, "papers": 1, "wechat": 1}
    assert [entry["title"] for entry in overview["recent_briefings"]][:2] == ["Reading List: AI Agents", "Digest: AI Weekly"]


def test_build_dashboard_overview_reports_missing_sources_and_orphan_markdown(tmp_path: Path) -> None:
    from ai_intel_station.adapters.web.service import build_dashboard_overview

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
    import ai_intel_station.collect.github as github_collect
    import ai_intel_station.collect.wechat as wechat_collect
    from ai_intel_station.adapters.web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    monkeypatch.setattr(github_collect, "run_gh", lambda cmd: (_ for _ in ()).throw(AssertionError("remote GitHub fetch should not run")))
    monkeypatch.setattr(wechat_collect, "fetch_article", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("remote WeChat fetch should not run")))

    items = list_library_items(output_root, keyword="agent", sources=["github"], since="2026-05-07")

    assert [item["title"] for item in items["items"]] == ["Claude Code", "agent-flow"]
    assert {item["source"] for item in items["items"]} == {"github"}


def test_get_library_item_detail_maps_local_metadata(tmp_path: Path) -> None:
    from ai_intel_station.adapters.web.service import get_library_item_detail

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
    from ai_intel_station.adapters.web.service import preview_briefing

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
    from ai_intel_station.adapters.web.service import save_briefing

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
    from ai_intel_station.cli import main

    output_root = tmp_path / "output"
    calls: list[Path] = []

    monkeypatch.setattr("ai_intel_station.cli.run_web_workspace", lambda current_output_root: calls.append(current_output_root))

    assert main(["web", "--output-root", str(output_root)]) == 0
    assert calls == [output_root]


def test_build_dashboard_overview_returns_empty_state_info_when_no_items(tmp_path: Path) -> None:
    """Test that dashboard overview indicates empty state when no items exist."""
    from ai_intel_station.adapters.web.service import build_dashboard_overview

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    overview = build_dashboard_overview(output_root)

    assert overview["total_items"] == 0
    assert overview["missing_sources"] == ["github", "papers", "wechat"]
    assert len(overview["orphan_markdown_paths"]) == 0


def test_list_library_items_returns_empty_list_when_no_items(tmp_path: Path) -> None:
    """Test that library returns empty list when no items exist."""
    from ai_intel_station.adapters.web.service import list_library_items

    output_root = tmp_path / "output"
    output_root.mkdir(parents=True)

    items = list_library_items(output_root, keyword="agent", sources=["github", "papers", "wechat"])

    assert items["items"] == []


def test_preview_briefing_handles_empty_items_gracefully(tmp_path: Path) -> None:
    """Test that briefing preview works with no items."""
    from ai_intel_station.adapters.web.service import preview_briefing

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
    from ai_intel_station.adapters.web.service import get_collect_form

    github_form = get_collect_form("github")
    field_names = [f["name"] for f in github_form["fields"]]

    assert "query" in field_names
    assert "search" in field_names
    assert "max" in field_names


def test_papers_collect_form_has_category_and_max_fields() -> None:
    """Test that papers collect form has category and max fields."""
    from ai_intel_station.adapters.web.service import get_collect_form

    papers_form = get_collect_form("papers")
    field_names = [f["name"] for f in papers_form["fields"]]

    assert "category" in field_names
    assert "max" in field_names


def test_collect_form_includes_field_labels_and_placeholders() -> None:
    """Test that collect forms include proper labels and placeholders."""
    from ai_intel_station.adapters.web.service import get_collect_form

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
    from ai_intel_station.adapters.web.service import get_collect_form

    unknown_form = get_collect_form("unsupported")
    assert unknown_form["id"] == "unsupported"
    assert unknown_form["label"] == "unsupported"
    assert unknown_form["fields"] == []


def test_run_collect_github_single_repo(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to GitHub collect for single repo mode."""
    import ai_intel_station.collect.github as github_collect

    called_with: list = []

    def mock_save_repo(owner: str, repo: str, output_dir: Path) -> None:
        called_with.append((owner, repo))
        return None

    monkeypatch.setattr(github_collect, "save_repo", mock_save_repo)
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect(
        "github",
        {"query": "anthropic/claude-code", "search": False, "max": 10},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert "anthropic/claude-code" in result["message"]
    assert called_with == [("anthropic", "claude-code")]


def test_run_collect_github_search_mode(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to GitHub search when search=True."""
    import ai_intel_station.collect.github as github_collect

    called_with: list = []

    def mock_run_gh(cmd: list[str]) -> str:
        called_with.append(cmd)
        return "[]"

    monkeypatch.setattr(github_collect, "run_gh", mock_run_gh)
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect(
        "github",
        {"query": "agent", "search": True, "max": 5},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert "agent" in result["message"]
    assert called_with == [[
        "search", "repos", "agent", "--sort", "updated", "--limit", "5",
        "--json", "name,owner,description,url,stargazersCount,createdAt,updatedAt",
    ]]
    snapshots = list((tmp_path / "output" / "github" / "_search").glob("agent-*"))
    assert len(snapshots) == 1
    assert (snapshots[0] / "search.md").is_file()


def test_run_collect_papers(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to papers collect."""
    import ai_intel_station.collect.papers as papers_collect

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
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect("papers", {"category": "cs.AI", "max": 3})
    assert result["status"] == "success"
    assert "cs.AI" in result["message"]
    assert called_with == [(["cs.AI"], 3)]
    assert len(save_called) == 1  # must persist, not just fetch


def test_run_collect_wechat(tmp_path: Path, monkeypatch) -> None:
    """Test that run_collect dispatches to WeChat collect with URL."""
    import ai_intel_station.collect.wechat as wechat_collect

    called_with: list = []

    async def mock_fetch(url: str, output_dir: Path | None = None) -> dict:
        called_with.append(url)
        return {"title": "Agent Overview", "url": url}

    monkeypatch.setattr(wechat_collect, "fetch_article", mock_fetch)
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect("wechat", {"url": "https://mp.weixin.qq.com/s/test"})
    assert result["status"] == "success"
    assert called_with == ["https://mp.weixin.qq.com/s/test"]


def test_run_collect_wechat_missing_url_returns_error(tmp_path: Path) -> None:
    """Test that WeChat collect returns error when URL is missing."""
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect("wechat", {"url": ""})
    assert result["status"] == "error"
    assert "URL" in result["message"]


# ---------------------------------------------------------------------------
# Library pagination tests
# ---------------------------------------------------------------------------

def test_list_library_items_pagination_returns_correct_slice(tmp_path: Path) -> None:
    """Test that list_library_items returns paginated results with metadata."""
    from ai_intel_station.adapters.web.service import list_library_items

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
    from ai_intel_station.adapters.web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    page1 = list_library_items(output_root, page=1, page_size=2)
    page2 = list_library_items(output_root, page=2, page_size=2)

    page1_ids = [item["output_path"] for item in page1["items"]]
    page2_ids = [item["output_path"] for item in page2["items"]]
    assert page1_ids != page2_ids or page1["total_count"] <= 2


def test_list_library_items_total_count_matches_all_results(tmp_path: Path) -> None:
    """Test that total_count equals all items without pagination."""
    from ai_intel_station.adapters.web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    result_all = list_library_items(output_root)
    result_page1 = list_library_items(output_root, page=1, page_size=100)

    assert result_page1["total_count"] == result_all["total_count"]


def test_list_library_items_page_size_change_resets_to_page_1(tmp_path: Path) -> None:
    """Test that changing page_size returns page 1 results."""
    from ai_intel_station.adapters.web.service import list_library_items

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
    from ai_intel_station.adapters.web.service import list_library_items

    output_root = tmp_path / "output"
    _seed_output_tree(output_root)

    agent_results = list_library_items(output_root, keyword="agent")
    empty_results = list_library_items(output_root, keyword="nonexistent-keyword-xyz")

    assert agent_results["total_count"] > 0
    assert empty_results["total_count"] == 0


def test_get_library_item_detail_returns_expanded_metadata(tmp_path: Path) -> None:
    """Test that get_library_item_detail returns item_type, published_at, and updated_at fields."""
    from ai_intel_station.adapters.web.service import get_library_item_detail

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
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect("twitter", {"query": "test"})
    assert result["status"] == "error"
    assert "Unknown source" in result["message"]
# WEB-COLLECT-PERSIST: align-web-collect-with-local-output-truth
# ---------------------------------------------------------------------------


def test_run_collect_github_writes_to_output_root(tmp_path: Path, monkeypatch) -> None:
    """GitHub single-repo collect MUST write to output_root/github, not /tmp."""
    import ai_intel_station.collect.github as github_collect

    captured: dict = {}

    def mock_save_repo(owner: str, repo: str, output_dir: Path) -> None:
        captured["output_dir"] = output_dir

    monkeypatch.setattr(github_collect, "save_repo", mock_save_repo)
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect(
        "github",
        {"query": "owner/repo", "search": False, "max": 10},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert captured["output_dir"] == tmp_path / "output" / "github"


def test_run_collect_papers_saves_to_output_root(tmp_path: Path, monkeypatch) -> None:
    """Papers collect MUST call save_papers() with output_root/papers."""
    import ai_intel_station.collect.papers as papers_collect

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
    from ai_intel_station.adapters.web.service import run_collect

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
    import ai_intel_station.collect.wechat as wechat_collect

    captured: dict = {}

    async def mock_fetch_article(url: str, output_dir: Path | None = None) -> dict:
        captured["url"] = url
        captured["output_dir"] = output_dir
        return {"title": "Test Article", "url": url}

    monkeypatch.setattr(wechat_collect, "fetch_article", mock_fetch_article)
    from ai_intel_station.adapters.web.service import run_collect

    result = run_collect(
        "wechat",
        {"url": "https://mp.weixin.qq.com/s/test"},
        output_root=tmp_path / "output",
    )
    assert result["status"] == "success"
    assert captured["url"] == "https://mp.weixin.qq.com/s/test"
    assert captured["output_dir"] == tmp_path / "output" / "wechat"
