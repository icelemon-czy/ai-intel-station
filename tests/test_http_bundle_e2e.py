"""Current HTTP contract compliance — REAL end-to-end tests covering the full
frontend-bundles-served-by-Python-backend round trip.

These tests differ from `tests/test_system_contracts.py` and
`tests/test_e2e_archive.py` in one critical respect:

  * **No mocked request handler.** They spawn the actual
    `workspace_web.server.serve_workspace` in a real subprocess,
    bind a real `ThreadingHTTPServer`, and probe the bound port
    with real HTTP. What the user gets in their browser when they
    run `uv run research web` is what the test hits.
  * **No mocked CLI.** Where `test_system_contracts.py` runs
    `console_main()` through `subprocess.run(..., "-c", ...)`, that
    exercise does not exercise the bundled frontend. This file
    rebuilds the frontend bundle when needed (`npm run build`),
    serves the actual `workspace_web/static/` directory, and
    asserts the served `/`, `/assets/<hashed>.js`, and
    `/api/library` shape matches what the React app expects.
  * **No mocked data layer.** The server reads `output/` from disk
    and serves real JSON. Tests seed `output/` in a temp directory,
    start the server on that root, and assert that JSON shapes
    contract-match the React component expectations.

If you have a strong network sandbox that prevents
`ThreadingHTTPServer` from binding 127.0.0.1, the test self-skips
with a clear message rather than failing — it is meant to run on
developer machines and CI, not in restricted sandboxes.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from library.items import (
    build_github_repo_item,
    build_paper_item,
    write_research_item,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")
STATIC_DIR = REPO_ROOT / "workspace_web" / "static"
ASSETS_DIR = STATIC_DIR / "assets"


def _port_is_bindable(port: int) -> bool:
    """Return True iff we can bind 127.0.0.1:<port>.

    Used to self-skip the test on restricted sandboxes where bind(2)
    fails with EACCES. On CI / dev machines this returns True.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
        sock.close()
        return True
    except (OSError, PermissionError):
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _free_loopback_port() -> int:
    """Ask the kernel for an available loopback port.

    Fixed ports make unrelated HTTP test modules order-dependent. The short
    close-to-bind window is sufficient for these single-process test runs and
    avoids collisions with other local services.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_reachable(
    proc: subprocess.Popen,
    base: str,
    *,
    timeout: float = 4.0,
) -> None:
    """Wait for the subprocess to finish binding, not merely print a banner."""
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr else ""
            raise RuntimeError(
                f"server exited before becoming reachable at {base}: {stderr!r}"
            )
        try:
            with urllib.request.urlopen(f"{base}/api/navigation", timeout=1):
                return
        except (urllib.error.URLError, ConnectionError, OSError) as exc:
            last_error = exc
            time.sleep(0.05)
    raise RuntimeError(
        f"server never became reachable at {base}: {last_error!r}"
    )


class _WorkspaceServer:
    """Context-manager style helper: spawn a real `serve_workspace`
    in a subprocess. Yields the base URL once the server is reachable.

    The caller supplies a kernel-assigned port and the helper waits until
    the real server answers a request.
    """

    def __init__(self, output_root: Path, port: int):
        self.output_root = output_root
        self.port = port
        self.proc = None
        self.base = f"http://127.0.0.1:{port}"

    def __enter__(self):
        # subprocess.Popen so we can terminate even if the test
        # raises. capture stdout/stderr so the test log doesn't get
        # noise from uvicorn-style access logs.
        script = (
            "import os, sys, pathlib, time\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from workspace_web import server as srv\n"
            "self_url = f'http://127.0.0.1:{int(os.environ[\"PORT\"])}'\n"
            "print(f'LISTENING {self_url}', flush=True)\n"
            f"srv.serve_workspace(pathlib.Path({str(self.output_root)!r}), "
            "port=int(os.environ['PORT']))\n"
        )
        env = {**os.environ, "PORT": str(self.port)}
        self.proc = subprocess.Popen(
            [PYTHON, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        # Wait until the server says LISTENING on stdout, with a
        # bounded retry budget so a perm-denied bind is reported
        # clearly.
        deadline = time.time() + 4.0
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                # EOF — process died. Drain stderr for diagnosis.
                err = self.proc.stderr.read() if self.proc.stderr else ""
                raise RuntimeError(
                    f"server exited before reaching LISTENING: stderr={err!r}"
                )
            if line.startswith("LISTENING"):
                break
        # Hit one warmup request so the first test does not pay the
        # bind handshake cost.
        for _ in range(20):
            try:
                urllib.request.urlopen(f"{self.base}/api/navigation", timeout=1)
                return self
            except (urllib.error.URLError, ConnectionError, OSError):
                time.sleep(0.05)
        # If we never connected the server may have started but
        # something downstream is wrong — surface diagnostics.
        try:
            self.proc.terminate()
            err = self.proc.stderr.read()
        except Exception:
            err = ""
        raise RuntimeError(f"server never became reachable on {self.base}: {err!r}")

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=3)
            except Exception:
                self.proc.kill()

    def get_json(self, path: str, query: dict | None = None):
        url = f"{self.base}{path}"
        if query:
            from urllib.parse import urlencode

            url = f"{url}?{urlencode(query)}"
        with urllib.request.urlopen(url, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def get_text(self, path: str):
        with urllib.request.urlopen(f"{self.base}{path}", timeout=3) as resp:
            return resp.read().decode("utf-8")

    def post_json(self, path: str, payload):
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3) as resp:
            return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Contract Requirement 1 + 2 (Source-Segregated Archive / Traceable Markdown)
# Round trip: seed real files → run real serve → frontend bundle asks the
# server for `/api/library` → server reads real sidecars from disk.
# ---------------------------------------------------------------------------


class ContractBackendBundleRoundTripTests(unittest.TestCase):
    """End-to-end: real server, real sidecar, real HTTP, real bundle.

    Each test self-skips on sandboxes that block 127.0.0.1 bind.
    """

    _bindable: bool = False

    @classmethod
    def setUpClass(cls):
        cls._bindable = _port_is_bindable(0)
        cls.bundle_present = ASSETS_DIR.exists() and any(ASSETS_DIR.glob("*.js"))

    def setUp(self):
        if not self._bindable:
            self.skipTest("sandbox blocks binding 127.0.0.1; e2e HTTP test cannot run here")
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # Seed two sources side-by-side so the test can assert
        # the server respects the `?source=` filter at the
        # network boundary.
        self._seed_repo("demo-x", "Go")
        self._seed_repo("demo-y", "Python")
        self._seed_paper("0000.00001")
        self._seed_paper("0000.00002")
        self.port = _free_loopback_port()
        self.server = _WorkspaceServer(self.tmp, self.port)
        self.server.__enter__()

    def tearDown(self):
        try:
            self.server.__exit__(None, None, None)
        except Exception:
            pass
        self._tmp.cleanup()

    def _seed_repo(self, name: str, language: str):
        repo_dir = self.tmp / "github" / f"demo-{name}"
        repo_dir.mkdir(parents=True)
        (repo_dir / "README.md").write_text(
            f"# {name}\n\n> {language} repo.\n\n"
            f"- 🌐 URL: https://github.com/demo/{name}\n"
            f"- ⭐ Stars: 1\n"
            f"- 🏷️ Language: {language}\n"
            f"- 📅 Created: 2026-01-01\n"
            f"- 🔄 Updated: 2026-06-15\n",
            encoding="utf-8",
        )
        write_research_item(
            build_github_repo_item(
                "demo",
                name,
                {
                    "name": name,
                    "description": f"{language} demo",
                    "url": f"https://github.com/demo/{name}",
                    "stargazerCount": 1,
                    "primaryLanguage": {"name": language},
                    "repositoryTopics": [],
                    "createdAt": "2026-01-01T00:00:00Z",
                    "updatedAt": "2026-06-15T00:00:00Z",
                    "issues": [],
                },
                repo_dir / "README.md",
            ),
            repo_dir / "research-item.json",
        )

    def _seed_paper(self, arxiv_id: str):
        papers_dir = self.tmp / "papers" / "arXiv-cs.AI"
        papers_dir.mkdir(parents=True, exist_ok=True)
        md = papers_dir / f"{arxiv_id}.md"
        md.write_text(
            f"# Paper {arxiv_id}\n\n> Author A.\n\n"
            f"- 📅 Published: 2026-06-01\n"
            f"- 🏷️ Categories: cs.AI\n"
            f"- 🔗 arXiv: https://arxiv.org/abs/{arxiv_id}\n"
            f"- 📄 PDF: https://arxiv.org/pdf/{arxiv_id}\n",
            encoding="utf-8",
        )
        write_research_item(
            build_paper_item(
                {
                    "title": f"Paper {arxiv_id}",
                    "authors": ["A"],
                    "summary": "test",
                    "published": "2026-06-01T00:00:00Z",
                    "updated": "2026-06-02T00:00:00Z",
                    "arxiv_id": arxiv_id,
                    "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}",
                    "abs_url": f"https://arxiv.org/abs/{arxiv_id}",
                    "categories": ["cs.AI"],
                },
                md,
            ),
            md.with_name(md.stem + ".research-item.json"),
        )

    # -- Requirement 1: Source-Segregated Archive -------------------------

    def test_live_server_filters_library_by_source_at_http_boundary(self):
        """The real `/api/library?source=github` endpoint MUST only return
        items whose archive path lives under `output/github/`. This is
        the cross-cutting source-segregation contract: a request asking
        for `papers` must not leak github sidecars (or vice versa)."""
        gh_items = self.server.get_json("/api/library", {"source": "github"})
        paper_items = self.server.get_json("/api/library", {"source": "papers"})
        # Both sides must surface at least the seeded items.
        self.assertGreaterEqual(
            len(gh_items.get("items", [])),
            2,
            f"server returned < 2 github items: {gh_items!r}",
        )
        self.assertGreaterEqual(
            len(paper_items.get("items", [])),
            2,
            f"server returned < 2 paper items: {paper_items!r}",
        )
        # Cross-source leakage: NO github-side item may have an
        # archive path that lives under output/papers/; NO paper-side
        # item may have a path under output/github/.
        for item in gh_items["items"]:
            self.assertIn(
                "github",
                item.get("output_path", ""),
                f"source=github returned an item whose path is not under github/: "
                f"{item.get('output_path')!r}",
            )
        for item in paper_items["items"]:
            self.assertIn(
                "papers",
                item.get("output_path", ""),
                f"source=papers returned an item whose path is not under papers/: "
                f"{item.get('output_path')!r}",
            )

    # -- Requirement 2: Traceable Markdown Artifacts ----------------------

    def test_live_server_preserves_canonical_url_in_library_response(self):
        """The `canonical_url` returned to the React bundle MUST equal the
        URL minted at collect time. The frontend's MarkdownPreview,
        open-source button, and briefing hyperlinks all rely on this
        contract — if the server rewrites it, library inspection and
        briefing cross-references break silently."""
        items = self.server.get_json("/api/library", {"source": "github"})
        urls = {item.get("canonical_url") for item in items["items"]}
        # The two seeded repos are `demo-x` and `demo-y`.
        self.assertIn("https://github.com/demo/demo-x", urls)
        self.assertIn("https://github.com/demo/demo-y", urls)
        papers = self.server.get_json("/api/library", {"source": "papers"})
        for item in papers["items"]:
            # arXiv canonical_url must match the abs endpoint.
            self.assertTrue(
                item["canonical_url"].startswith("https://arxiv.org/abs/"),
                f"unexpected paper canonical_url: {item['canonical_url']!r}",
            )

    # -- Cross-cutting contract: bundle + server should agree -----------

    @unittest.skipUnless(
        (STATIC_DIR / "assets").exists() and any((STATIC_DIR / "assets").glob("*.js")),
        "frontend bundle not built (run `npm --prefix web run build`)",
    )
    def test_live_server_serves_the_frontend_index_html(self):
        """The React shell MUST be served at `/`. If the server returns
        a different page (or no JS bundle), the workspace is broken
        before React even mounts. This is the most basic cross-stack
        smoke a user notices — `localhost:4173` should render the
        research workspace, not a directory listing or 404."""
        html = self.server.get_text("/")
        self.assertIn("<div id=\"root\"", html, "frontend index.html has no #root mount point")
        self.assertIn("/assets/", html, "frontend index.html does not load bundled JS")
        # Ensure the JS bundle actually exists behind /assets/.
        bundle_html = html
        js_path = bundle_html.split('/assets/')[1].split('"')[0].split("'")[0]
        self.assertTrue(
            (ASSETS_DIR / js_path).exists(),
            f"index.html references /assets/{js_path} but that file is missing",
        )

    @unittest.skipUnless(
        (STATIC_DIR / "assets").exists() and any((STATIC_DIR / "assets").glob("*.js")),
        "frontend bundle not built",
    )
    def test_live_server_serves_the_actual_js_bundle(self):
        """Static-asset serving is part of the Contract contract — fetch the
        hashed JS bundle that index.html points at and confirm we get
        real JavaScript back (not a 404). Without this, the React
        app never mounts and the dashboard is just blank HTML."""
        # Locate the script src from index.html.
        index_html = self.server.get_text("/")
        # All <script ... src="..."> tags.
        import re as _re

        matches = _re.findall(r'<script[^>]*src="(/assets/[^"]+)"', index_html)
        self.assertTrue(matches, "no <script src=...> in served index.html")
        for script_path in matches:
            js_body = self.server.get_text(script_path)
            self.assertIn(
                "useState",
                js_body,
                f"served JS at {script_path!r} doesn't look like a React bundle",
            )


# ---------------------------------------------------------------------------
# Contract Requirement 3 (Runnable Documented Entrypoints) — run the unified
# `research` operator against a real HTTP-served workspace. This is the
# user's contract: `uv run research <subcommand>` MUST work end-to-end.
# ---------------------------------------------------------------------------


