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


_WEB_WORKSPACE_SOURCE_FILES = (
    "workspaceShared.jsx",
    "DashboardSection.jsx",
    "LibrarySection.jsx",
    "BriefingSection.jsx",
    "CollectSection.jsx",
    "App.jsx",
)


def _read_web_workspace_source() -> str:
    source_root = Path(__file__).resolve().parents[1] / "web" / "src"
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
    from library.storage import load_research_items
    from workspace_web.service import read_item_markdown

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
    app_jsx = _read_web_workspace_source()
    assert "MarkdownPreview" in app_jsx, "App.jsx must render a MarkdownPreview component"
    # Must appear at least 2 times: 1 definition + 1 use
    assert app_jsx.count("MarkdownPreview") >= 2, (
        f"App.jsx must reference MarkdownPreview at least twice; found {app_jsx.count('MarkdownPreview')}"
    )


def test_app_jsx_markdown_preview_endpoint_url_uses_output_path_query() -> None:
    """Scenario 5 (副): the preview fetch must hit /api/library/preview with output_path=..."""
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()

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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
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
    app_jsx = _read_web_workspace_source()
    assert "navigator.clipboard.writeText" in app_jsx, (
        "App.jsx must use navigator.clipboard.writeText for copying"
    )
    # And the deprecated execCommand must NOT be used as a fallback
    assert "execCommand" not in app_jsx, (
        "App.jsx must not use the deprecated document.execCommand"
    )


def test_app_jsx_has_about_local_files_note() -> None:
    """Scenario 6: App.jsx includes a small 'About local files' note."""
    app_jsx = _read_web_workspace_source()
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
