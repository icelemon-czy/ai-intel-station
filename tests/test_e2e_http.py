from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path


def _can_bind_loopback() -> bool:
    """Sandbox/limited environments refuse socket bind; skip live tests there."""
    try:
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0))
        return True
    except (PermissionError, OSError):
        return False


@unittest.skipUnless(_can_bind_loopback(), "sandbox blocks loopback bind")
class WorkspaceHttpEndToEndTests(unittest.TestCase):
    """Real HTTP loopback tests against the actual ThreadingHTTPServer used by
    ``research web``. No fake handler, no monkeypatching of do_GET/do_POST."""

    @classmethod
    def setUpClass(cls) -> None:
        from workspace_web.server import _create_handler

        cls._tmp = tempfile.TemporaryDirectory()
        out = Path(cls._tmp.name)
        # Seed one sidecar so /api/library returns something real.
        from library.items import ResearchItem, write_research_item

        repo_md = out / "github" / "demo-demo-repo" / "README.md"
        repo_md.parent.mkdir(parents=True)
        repo_md.write_text(
            "# demo-repo\n\n> Demo.\n\n"
            "- 🌐 URL: https://github.com/demo/demo-repo\n"
            "- ⭐ Stars: 7\n"
            "- 🏷️ Language: Python\n"
            "- 📅 Created: 2026-01-01\n"
            "- 🔄 Updated: 2026-06-15\n",
            encoding="utf-8",
        )
        item = ResearchItem(
            source="github",
            item_type="repository",
            title="demo-repo",
            canonical_url="https://github.com/demo/demo-repo",
            output_path=str(repo_md),
            metadata={"stargazer_count": 7},
        )
        write_research_item(item, repo_md.parent / "research-item.json")

        cls._server = ThreadingHTTPServer(("127.0.0.1", 0), _create_handler(out))
        cls._port = cls._server.server_address[1]
        cls._thread = threading.Thread(target=cls._server.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls._server.shutdown()
        cls._server.server_close()
        cls._tmp.cleanup()

    def _get(self, path: str) -> tuple[int, dict]:
        with urllib.request.urlopen(f"http://127.0.0.1:{self._port}{path}") as r:
            return r.status, json.loads(r.read())

    def _post(self, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = json.dumps(payload or {}).encode("utf-8")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self._port}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())

    def test_get_navigation(self) -> None:
        status, body = self._get("/api/navigation")
        self.assertEqual(status, 200)
        self.assertIsInstance(body, list)
        self.assertEqual(
            [section["id"] for section in body],
            ["dashboard", "library", "briefing", "collect"],
        )

    def test_get_dashboard_includes_seeded_repo(self) -> None:
        status, body = self._get("/api/dashboard")
        self.assertEqual(status, 200)
        # Seeded repo should appear in the dashboard summary.
        self.assertGreaterEqual(body.get("total_items", 0), 1)

    def test_get_library_returns_seeded_item(self) -> None:
        status, body = self._get("/api/library")
        self.assertEqual(status, 200)
        titles = [item.get("title") for item in body.get("items", [])]
        self.assertIn("demo-repo", titles)

    def test_get_discover_status(self) -> None:
        status, body = self._get("/api/discover/status")
        self.assertEqual(status, 200)
        # Either has_run or empty.
        self.assertIn("has_run", body)

    def test_post_discover_run_returns_job_id(self) -> None:
        # Sync mode returns the full report synchronously.  Point at a missing
        # temporary config so this HTTP contract never starts a live sweep.
        status, body = self._post(
            "/api/discover/run?sync=1",
            {"config_path": str(Path(self._tmp.name) / "missing-discovery.yaml")},
        )
        self.assertEqual(status, 200)
        self.assertEqual(body.get("status"), "config_error")

    def test_get_unknown_api_returns_404(self) -> None:
        import urllib.error

        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self._get("/api/does-not-exist")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
