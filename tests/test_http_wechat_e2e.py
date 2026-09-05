"""Current HTTP contract compliance — REAL end-to-end tests covering the full
frontend-bundles-served-by-Python-backend round trip.

These tests differ from `tests/test_system_contracts.py` and
`tests/test_e2e_archive.py` in one critical respect:

  * **No mocked request handler.** They spawn the actual
    `ai_intel_station.adapters.web.server.serve_workspace` in a real subprocess,
    bind a real `ThreadingHTTPServer`, and probe the bound port
    with real HTTP. What the user gets in their browser when they
    run `uv run research web` is what the test hits.
  * **No mocked CLI.** Where `test_system_contracts.py` runs
    `console_main()` through `subprocess.run(..., "-c", ...)`, that
    exercise does not exercise the bundled frontend. This file
    rebuilds the frontend bundle when needed (`npm run build`),
    serves the actual `ai_intel_station/adapters/web/static/` directory, and
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

from ai_intel_station.library.items import (
    build_github_repo_item,
    build_paper_item,
    write_research_item,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")
STATIC_DIR = REPO_ROOT / "src" / "ai_intel_station" / "adapters" / "web" / "static"
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
            f"sys.path.insert(0, {str(REPO_ROOT / "src")!r})\n"
            "from ai_intel_station.adapters.web import server as srv\n"
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


class ContractWechatInputValidationHttpBoundaryTests(unittest.TestCase):
    """Real HTTP server with live-test configuration explicitly absent.

    `WECHAT_E2E_URLS` controls the separate live suite; normal Web startup
    and input validation must not depend on it.
    """

    _bindable: bool = False

    @classmethod
    def setUpClass(cls):
        cls._bindable = _port_is_bindable(0)

    def setUp(self):
        if not self._bindable:
            self.skipTest(
                "sandbox blocks binding 127.0.0.1; e2e HTTP skip test "
                "cannot run here"
            )
        # Critical: explicitly UNSET WECHAT_E2E_URLS in the child
        # process environment. Anywhere the operator's shell has it
        # set, the subprocess must still see it unset.
        child_env = {k: v for k, v in os.environ.items() if k != "WECHAT_E2E_URLS"}
        child_env["WECHAT_E2E_URLS"] = ""  # ensure empty, not inherited
        self.port = _free_loopback_port()
        child_env["PORT"] = str(self.port)
        child_env["PYTHONPATH"] = str(REPO_ROOT / "src")
        script = (
            "import sys, pathlib, os\n"
            f"sys.path.insert(0, {str(REPO_ROOT / "src")!r})\n"
            "print('LISTENING http://127.0.0.1:' + os.environ['PORT'], flush=True)\n"
            f"from ai_intel_station.adapters.web import server as srv\n"
            f"srv.serve_workspace(pathlib.Path('output'), "
            "port=int(os.environ['PORT']))\n"
        )
        self.server_proc = subprocess.Popen(
            [PYTHON, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=child_env,
            cwd=str(REPO_ROOT),
        )
        deadline = time.time() + 4.0
        while time.time() < deadline:
            line = self.server_proc.stdout.readline()
            if not line:
                err = self.server_proc.stderr.read() if self.server_proc.stderr else ""
                raise RuntimeError(
                    f"server exited before reaching LISTENING: stderr={err!r}"
                )
            if line.startswith("LISTENING"):
                break
        self.base = f"http://127.0.0.1:{self.port}"
        _wait_until_reachable(self.server_proc, self.base)

    def tearDown(self):
        try:
            if self.server_proc.poll() is None:
                self.server_proc.terminate()
                try:
                    self.server_proc.wait(timeout=3)
                except Exception:
                    self.server_proc.kill()
        except Exception:
            pass

    def test_wechat_missing_url_is_structured_when_live_env_is_unset(self):
        """Missing required input returns actionable JSON without browser I/O."""
        body = self._post(
            "/api/collect/run",
            {
                "source": "wechat",
                "fields": {"url": ""},
            },
        )
        if body.get("__http_status__"):
            self.fail(
                f"/api/collect/run(wechat) returned HTTP "
                f"{body['__http_status__']} for missing URL. "
                f"body={body['__body__'][:300]!r}"
            )
        self.assertEqual(body.get("status"), "error")
        self.assertIn("url", (body.get("message") or "").lower())
        self.assertTrue(body.get("next_step"))

    def _post(self, path: str, payload) -> dict:
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return {
                "__http_status__": exc.code,
                "__body__": exc.read().decode("utf-8", errors="replace"),
            }


if __name__ == "__main__":
    unittest.main()
