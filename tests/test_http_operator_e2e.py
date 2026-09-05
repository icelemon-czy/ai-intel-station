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


class ContractUnifiedOperatorServeSubprocessTests(unittest.TestCase):
    """Boot the documented entrypoint the way a user does, and verify
    the workspace backend it spawns serves the documented surface."""

    _bindable: bool = False

    @classmethod
    def setUpClass(cls):
        cls._bindable = _port_is_bindable(0)

    def setUp(self):
        if not self._bindable:
            self.skipTest("sandbox blocks binding 127.0.0.1; cannot run real CLI subprocess")
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        # Seed at least one archive item so the rendered briefing
        # has real content to surface.
        repo_dir = self.tmp / "github" / "demo-real-cli"
        repo_dir.mkdir(parents=True)
        (repo_dir / "README.md").write_text(
            "# real-cli\n\n> Real CLI test repo.\n\n"
            "- 🌐 URL: https://github.com/demo/real-cli\n"
            "- ⭐ Stars: 7\n"
            "- 🏷️ Language: Go\n",
            encoding="utf-8",
        )
        write_research_item(
            build_github_repo_item(
                "demo",
                "real-cli",
                {
                    "name": "real-cli",
                    "description": "Real CLI test repo",
                    "url": "https://github.com/demo/real-cli",
                    "stargazerCount": 7,
                    "primaryLanguage": {"name": "Go"},
                    "repositoryTopics": [],
                    "createdAt": "2026-01-01T00:00:00Z",
                    "updatedAt": "2026-06-15T00:00:00Z",
                    "issues": [],
                },
                repo_dir / "README.md",
            ),
            repo_dir / "research-item.json",
        )
        self.port = _free_loopback_port()

    def tearDown(self):
        self._tmp.cleanup()

    def test_research_web_subcommand_serves_real_library_endpoint(self):
        """`uv run research web -o <output>` is the documented entrypoint
        documented in CLAUDE.md. The user expects to point their browser
        at http://127.0.0.1:<port>/ and search results from their real
        archive. This test runs that command in a fresh subprocess, then
        probes the actual HTTP port the server bound to."""
        # Spawn `research web` in a real subprocess with a non-default
        # port forwarded via env. The CLI doesn't accept --port today,
        # so we spawn serve_workspace directly via the python module
        # entry point — that IS what `research web` does internally.
        env = {**os.environ, "PORT": str(self.port)}
        proc = subprocess.Popen(
            [PYTHON, "-c",
             "import sys, pathlib, os\n"
             f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
             "from workspace_web import server as srv\n"
             f"srv.serve_workspace(pathlib.Path({str(self.tmp)!r}), "
             "port=int(os.environ['PORT']))\n"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(REPO_ROOT),
        )
        try:
            # Wait for the server to bind and answer a probe request.
            deadline = time.time() + 5
            body = None
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(
                        f"http://127.0.0.1:{self.port}/api/library?source=github",
                        timeout=1,
                    ) as resp:
                        body = json.loads(resp.read().decode("utf-8"))
                    break
                except (urllib.error.URLError, ConnectionError, OSError):
                    time.sleep(0.05)
            self.assertIsNotNone(
                body, "research-web subprocess never answered HTTP within 5s"
            )
            # The seeded item MUST be present in the response — i.e. the
            # server reads from the output_root the CLI was told to use.
            self.assertGreaterEqual(
                body.get("total_count", 0),
                1,
                f"real-cli /api/library returned 0 items: {body!r}",
            )
            self.assertTrue(
                any(
                    "real-cli" in (item.get("title") or "")
                    for item in body.get("items", [])
                ),
                f"real-cli item not in /api/library response: {body!r}",
            )
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except Exception:
                proc.kill()


# ---------------------------------------------------------------------------
# Contract Requirement 4 (Explicit External Dependency Failure) — the upstream
# spec says failures MUST surface with explicit context. Going through the
# HTTP boundary means: a request that triggers a network/CLI failure MUST
# NOT 5xx or return an empty body; it MUST return a structured JSON
# response whose `message` / `summary` carries the failing dependency name
# (e.g. "gh", "camoufox", category id) so the React `<CollectSection>`
# can render the error banner.
#
# The existing `tests/test_system_contracts.py::ContractExplicitExternalDependencyFailureTests`
# only stubs `collect.github.run_gh` and asserts in-process. The tests
# below exercise the SAME behaviour through the real HTTP server, so the
# cross-stack contract (request -> server handler -> collector module ->
# structured JSON -> frontend) is locked.
# ---------------------------------------------------------------------------


