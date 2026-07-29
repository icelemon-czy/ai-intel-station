"""Real e2e tests for workspace_web.service — the dashboard / library /
briefing / collect endpoints. No mocks: build a real on-disk output tree
(seeded by writing actual ResearchItem sidecars + markdown), then exercise
each endpoint through a real ThreadingHTTPServer (skipped when the sandbox
forbids socket bind)."""

from __future__ import annotations

import io
import socket
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer
from pathlib import Path

from library.items import (
    ResearchItem,
    write_research_item,
    write_research_items_jsonl,
)
from workspace_web.server import _create_handler


def _can_bind_loopback() -> bool:
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
        return True
    except (PermissionError, OSError):
        return False


def _seed_output_tree(output_root: Path) -> None:
    """Create a realistic mix of sidecars so the dashboard has interesting data."""
    # GitHub: a real-style repo sidecar.
    gh_dir = output_root / "github" / "demo-repo"
    gh_dir.mkdir(parents=True)
    (gh_dir / "README.md").write_text(
        "# demo-repo\n\n> Demo.\n\n"
        "- 🌐 URL: https://github.com/demo/demo-repo\n"
        "- ⭐ Stars: 7\n"
        "- 🏷️ Language: Python\n"
        "- 📅 Created: 2026-01-01\n"
        "- 🔄 Updated: 2026-06-15\n",
        encoding="utf-8",
    )
    write_research_item(
        ResearchItem(
            source="github",
            item_type="repository",
            title="demo-repo",
            canonical_url="https://github.com/demo/demo-repo",
            output_path=str(gh_dir / "README.md"),
            tags=["demo", "python"],
            metadata={"stargazer_count": 7, "primary_language": "Python"},
        ),
        gh_dir / "research-item.json",
    )

    # GitHub: search results in JSONL form.
    search_dir = output_root / "github" / "agent-harness"
    search_dir.mkdir(parents=True)
    (search_dir / "search.md").write_text("# Search: agent harness\n\nFound 2\n", encoding="utf-8")
    write_research_items_jsonl(
        [
            ResearchItem(
                source="github",
                item_type="search-result",
                title="harness-alpha",
                canonical_url="https://github.com/a/harness-alpha",
                output_path=str(search_dir / "search.md"),
                metadata={"query": "agent harness", "stargazer_count": 100},
            ),
            ResearchItem(
                source="github",
                item_type="search-result",
                title="harness-beta",
                canonical_url="https://github.com/b/harness-beta",
                output_path=str(search_dir / "search.md"),
                metadata={"query": "agent harness", "stargazer_count": 50},
            ),
        ],
        search_dir / "research-items.jsonl",
    )

    # Papers
    papers_dir = output_root / "papers" / "arXiv-cs.AI"
    papers_dir.mkdir(parents=True)
    paper_md = papers_dir / "01-Sample Paper.md"
    paper_md.write_text(
        "# Sample Paper\n\n"
        "> **Authors:** Alice, Bob\n\n"
        "- 📅 Published: 2026-06-01\n"
        "- 🏷️ Categories: cs.AI\n"
        "- 🔗 arXiv: https://arxiv.org/abs/2606.99999\n"
        "- 📄 PDF: https://arxiv.org/pdf/2606.99999\n\n"
        "## Abstract\n\nWe test round-trip.\n",
        encoding="utf-8",
    )
    write_research_item(
        ResearchItem(
            source="papers",
            item_type="paper",
            title="Sample Paper",
            canonical_url="https://arxiv.org/abs/2606.99999",
            output_path=str(paper_md),
            tags=["cs.AI"],
            metadata={"pdf_url": "https://arxiv.org/pdf/2606.99999"},
        ),
        paper_md.with_name(paper_md.stem + ".research-item.json"),
    )

    # Briefing
    briefing_dir = output_root / "briefing" / "reading-lists"
    briefing_dir.mkdir(parents=True)
    (briefing_dir / "daily-2026-06-15.md").write_text(
        "# Reading List: daily-2026-06-15\n", encoding="utf-8"
    )


# ─────────────────────────────────────────────────────────────────────────
# Direct function tests (always run, no socket required)
# ─────────────────────────────────────────────────────────────────────────


class ServiceDirectTests(unittest.TestCase):
    """Exercise workspace_web.service.* without going through HTTP."""

    def test_build_dashboard_overview_with_seeded_tree(self) -> None:
        from workspace_web.service import build_dashboard_overview

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            overview = build_dashboard_overview(output_root)

        self.assertGreaterEqual(overview["total_items"], 3)  # 1 repo + 2 search + 1 paper
        self.assertIn("github", overview["source_counts"])
        self.assertEqual(overview["source_counts"]["github"], 3)
        self.assertEqual(overview["source_counts"]["papers"], 1)
        self.assertEqual(overview["source_counts"].get("wechat", 0), 0)
        # No wechat items seeded → wechat is missing.
        self.assertIn("wechat", overview["missing_sources"])
        # recent_briefings should include the one we wrote.
        self.assertEqual(len(overview["recent_briefings"]), 1)
        self.assertIn("daily-2026-06-15.md", overview["recent_briefings"][0]["path"])

    def test_build_dashboard_overview_empty_archive_returns_empty_state(self) -> None:
        from workspace_web.service import build_dashboard_overview

        with tempfile.TemporaryDirectory() as tmp:
            overview = build_dashboard_overview(Path(tmp))
        self.assertEqual(overview["total_items"], 0)
        self.assertIn("empty_state", overview)
        self.assertGreater(len(overview["empty_state"]["next_steps"]), 0)

    def test_list_library_items_returns_seeded_repo(self) -> None:
        from workspace_web.service import list_library_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            payload = list_library_items(output_root, page=1, page_size=10, sources=None)
        self.assertEqual(payload["total_count"], 4)
        self.assertEqual(payload["page"], 1)
        self.assertEqual(payload["total_pages"], 1)
        titles = [item["title"] for item in payload["items"]]
        self.assertIn("demo-repo", titles)
        self.assertIn("Sample Paper", titles)

    def test_list_library_items_filters_by_source(self) -> None:
        from workspace_web.service import list_library_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            payload = list_library_items(
                output_root, page=1, page_size=10, sources=["github"]
            )
        self.assertEqual(payload["total_count"], 3)

    def test_list_library_items_pagination(self) -> None:
        from workspace_web.service import list_library_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            payload = list_library_items(output_root, page=1, page_size=2)
        self.assertEqual(payload["total_count"], 4)
        self.assertEqual(payload["total_pages"], 2)
        self.assertEqual(len(payload["items"]), 2)

    def test_get_library_item_detail_known_item(self) -> None:
        from workspace_web.service import get_library_item_detail

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            # The output_path must be relative to output_root.
            detail = get_library_item_detail(
                output_root, "github/demo-repo/README.md"
            )
        self.assertIsNotNone(detail, "expected detail for seeded item")
        if detail:
            self.assertEqual(detail["title"], "demo-repo")
            self.assertEqual(detail["source"], "github")

    def test_get_library_item_detail_unknown_returns_none(self) -> None:
        from workspace_web.service import get_library_item_detail

        with tempfile.TemporaryDirectory() as tmp:
            detail = get_library_item_detail(Path(tmp), "github/missing/README.md")
        self.assertIsNone(detail)

    def test_read_item_markdown_returns_body(self) -> None:
        from workspace_web.service import read_item_markdown

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            body, mime = read_item_markdown(output_root, "github/demo-repo/README.md")
        self.assertIn("demo-repo", body)
        self.assertIn("text/markdown", mime)

    def test_read_item_markdown_refuses_unknown_path(self) -> None:
        from workspace_web.service import read_item_markdown

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(Exception) as ctx:
                read_item_markdown(Path(tmp), "github/missing/README.md")
        # Either FileNotFoundError ("not a known archive entry") or PreviewError
        # ("Refusing to read outside output_root"). Both signal refusal.
        msg = str(ctx.exception).lower()
        self.assertTrue(
            "not a known" in msg or "refusing" in msg,
            f"unexpected exception text: {ctx.exception}",
        )

    def test_preview_briefing_returns_markdown(self) -> None:
        from workspace_web.service import preview_briefing

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            buf = io.StringIO()
            with redirect_stdout(buf):
                # No keyword → query returns all matching items in the source.
                result = preview_briefing(
                    output_root,
                    mode="reading-list",
                    keyword="",
                    sources=["github"],
                )
        self.assertIn("Reading List", result["content"])
        self.assertIn("harness-alpha", result["content"])
        self.assertEqual(result["item_count"], 3)  # 1 repo + 2 search

    def test_save_briefing_writes_file(self) -> None:
        from workspace_web.service import save_briefing

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            _seed_output_tree(output_root)
            result = save_briefing(
                output_root,
                mode="reading-list",
                keyword="",
                sources=["github"],
            )
            # File exists and contains the title.
            path = Path(result["path"])
            self.assertTrue(path.is_file(), f"expected briefing at {path}")
            content = path.read_text(encoding="utf-8")
            self.assertIn("harness-alpha", content)

    def test_run_collect_validates_source(self) -> None:
        from workspace_web.service import run_collect

        # Unknown source should return a structured error, not raise.
        with tempfile.TemporaryDirectory() as tmp:
            result = run_collect("bogus", {}, output_root=Path(tmp))
        self.assertEqual(result["status"], "error")
        self.assertIn("not supported", result["summary"])

    def test_run_collect_wraps_github_network_failure(self) -> None:
        """GitHub collect must NOT 500 when `gh` is missing or the network
        fails — the front-end renders structured errors via the same
        ``_format_collect_result`` shape used for happy-path responses."""
        import collect.github as gh_collect
        import workspace_web.service as service

        original_run_gh = gh_collect.run_gh
        gh_collect.run_gh = lambda *args, **kwargs: exec(
            'raise RuntimeError("gh failed: command not found")'
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = service.run_collect(
                    "github",
                    {"query": "demo/demo", "max": 10, "search": False},
                    output_root=Path(tmp),
                )
        finally:
            gh_collect.run_gh = original_run_gh

        # The endpoint must return a structured error, not raise.
        self.assertEqual(result["status"], "error")
        self.assertIn("github", result["source"])
        # The user-facing message must NOT be a Python traceback.
        self.assertNotIn("Traceback", result["message"])
        # Must contain the actionable next_step.
        self.assertIn("next_step", result)
        self.assertGreater(len(result["next_step"]), 0)

    def test_run_collect_wraps_arxiv_failure(self) -> None:
        """arXiv fetch errors become structured results, not 500s."""
        import collect.papers as papers_collect
        import workspace_web.service as service

        original = papers_collect.fetch_papers_by_category
        papers_collect.fetch_papers_by_category = (
            lambda categories, max_results, **_kwargs: exec(
                'raise RuntimeError("arXiv timeout")'
            )
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = service.run_collect(
                    "papers",
                    {"category": "cs.AI", "max": 5},
                    output_root=Path(tmp),
                )
        finally:
            papers_collect.fetch_papers_by_category = original

        self.assertEqual(result["status"], "error")
        self.assertIn("papers", result["source"])
        self.assertIn("arXiv", result["message"])

    def test_run_collect_rejects_unknown_arxiv_category_without_writing(self) -> None:
        """Invalid category input is an explicit source error, not empty success."""
        import workspace_web.service as service

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            result = service.run_collect(
                "papers",
                {"category": "cs.UNKNOWN", "max": 5},
                output_root=output_root,
            )

            self.assertEqual(result["status"], "error")
            self.assertEqual(result["item_count"], 0)
            self.assertIn("cs.UNKNOWN", result["message"])
            self.assertFalse((output_root / "papers" / "cs.UNKNOWN").exists())

    def test_run_collect_wraps_wechat_failure(self) -> None:
        """WeChat fetch errors become structured results, not 500s."""
        import collect.wechat as wechat_collect
        import workspace_web.service as service

        original = wechat_collect.fetch_article
        wechat_collect.fetch_article = (
            lambda url, output_dir: exec(
                'raise RuntimeError("camoufox not installed")'
            )
        )
        try:
            with tempfile.TemporaryDirectory() as tmp:
                result = service.run_collect(
                    "wechat",
                    {"url": "https://mp.weixin.qq.com/s/test"},
                    output_root=Path(tmp),
                )
        finally:
            wechat_collect.fetch_article = original

        self.assertEqual(result["status"], "error")
        self.assertIn("wechat", result["source"])
        self.assertIn("camoufox", result["message"])

    def test_list_collect_sources_returns_known_sources(self) -> None:
        from workspace_web.service import list_collect_sources

        sources = list_collect_sources()
        ids = [s["id"] for s in sources]
        self.assertIn("github", ids)
        self.assertIn("papers", ids)
        self.assertIn("wechat", ids)

    def test_get_collect_form_for_github(self) -> None:
        from workspace_web.service import get_collect_form

        form = get_collect_form("github")
        self.assertIn("GitHub", form["label"])
        self.assertGreater(len(form["fields"]), 0)
        # github form is the search-by-keyword variant — assert its real shape.
        names = [f["name"] for f in form["fields"]]
        self.assertIn("query", names)


# ─────────────────────────────────────────────────────────────────────────
# HTTP-loopback tests (skipped in sandboxes that block bind)
# ─────────────────────────────────────────────────────────────────────────


@unittest.skipUnless(_can_bind_loopback(), "sandbox blocks loopback bind")
class ServiceHttpEndToEndTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.output_root = Path(self._tmp.name)
        _seed_output_tree(self.output_root)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _create_handler(self.output_root))
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._tmp.cleanup()

    def _get(self, path: str) -> tuple[int, dict]:
        import json
        import urllib.request

        with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}") as r:
            return r.status, json.loads(r.read())

    def _post(self, path: str, payload: dict | None = None) -> tuple[int, dict]:
        import json
        import urllib.request

        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())

    def test_get_dashboard_returns_seeded_totals(self) -> None:
        status, body = self._get("/api/dashboard")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(body["total_items"], 3)
        self.assertIn("github", body["source_counts"])

    def test_get_library_returns_seeded_items(self) -> None:
        status, body = self._get("/api/library")
        self.assertEqual(status, 200)
        titles = [item["title"] for item in body["items"]]
        self.assertIn("demo-repo", titles)
        self.assertIn("Sample Paper", titles)

    def test_get_library_item_returns_detail(self) -> None:
        status, body = self._get("/api/library/item?output_path=github/demo-repo/README.md")
        self.assertEqual(status, 200)
        self.assertEqual(body["title"], "demo-repo")

    def test_get_collect_sources(self) -> None:
        status, body = self._get("/api/collect/sources")
        self.assertEqual(status, 200)
        ids = [s["id"] for s in body]
        self.assertIn("github", ids)

    def test_get_collect_form_for_papers(self) -> None:
        status, body = self._get("/api/collect/form/papers")
        self.assertEqual(status, 200)
        self.assertEqual(body["id"], "papers")
        self.assertIn("arXiv", body["label"])
        self.assertIn("category", [field["name"] for field in body["fields"]])

    def test_get_briefing_metadata(self) -> None:
        status, body = self._get("/api/briefing/metadata")
        self.assertEqual(status, 200)
        self.assertEqual(set(body), {"flow_notes", "mode_purposes", "action_purposes"})
        self.assertEqual(set(body["mode_purposes"]), {"digest", "reading-list"})
        self.assertEqual(set(body["action_purposes"]), {"preview", "save"})
        self.assertIn("input_source", body["flow_notes"])

    def test_post_briefing_preview_returns_markdown_without_saving(self) -> None:
        briefing_root = self.output_root / "briefing"
        before = sorted(briefing_root.rglob("*.md")) if briefing_root.exists() else []
        status, body = self._post(
            "/api/briefing/preview",
            {"mode": "reading-list", "keyword": "", "sources": ["github"]},
        )
        self.assertEqual(status, 200)
        self.assertIn("Reading List", body["content"])
        self.assertGreater(body["item_count"], 0)
        after = sorted(briefing_root.rglob("*.md")) if briefing_root.exists() else []
        self.assertEqual(after, before)

    def test_post_briefing_save_creates_file(self) -> None:
        status, body = self._post(
            "/api/briefing/save",
            {"mode": "reading-list", "keyword": "", "sources": ["github"]},
        )
        self.assertEqual(status, 200)
        path = Path(body["path"])
        self.assertTrue(path.is_file(), f"expected briefing at {path}")

    def test_post_run_collect_unknown_source_returns_error_json(self) -> None:
        status, body = self._post(
            "/api/collect/run",
            {"source": "bogus", "fields": {}},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "error")
        self.assertEqual(body["source"], "bogus")
        self.assertTrue(body["summary"])
        self.assertTrue(body["next_step"])


if __name__ == "__main__":
    unittest.main()
