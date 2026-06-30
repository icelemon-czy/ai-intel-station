from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workspace_web.server import _create_handler
from workspace_web.service import discover_status_payload, run_discover_from_request


class _WFile:
    """Minimal file-like object that records bytes written by the handler."""

    def __init__(self) -> None:
        self.body = bytearray()

    def write(self, data: bytes) -> int:
        self.body.extend(data)
        return len(data)


class _RFile:
    """Minimal file-like object that returns a single fixed payload."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self, length: int = -1) -> bytes:
        if length < 0 or length >= len(self._payload):
            data = self._payload
            self._payload = b""
            return data
        data = self._payload[:length]
        self._payload = self._payload[length:]
        return data


def _make_handler(method: str, path: str, payload: dict | None = None):
    """Construct a BaseHTTPRequestHandler subclass instance with the fields
    ``do_GET`` / ``do_POST`` need, bypassing ``BaseRequestHandler.__init__``."""
    handler_cls = _create_handler(output_root=Path(tempfile.gettempdir()) / "discovery_test")

    payload_bytes = json.dumps(payload or {}).encode("utf-8")
    wfile = _WFile()

    class FakeHandler(handler_cls):  # type: ignore[misc]
        pass

    handler = FakeHandler.__new__(FakeHandler)
    handler.command = method
    handler.path = path
    handler.request_version = "HTTP/1.1"
    handler.headers = {
        "Content-Length": str(len(payload_bytes)),
        "Content-Type": "application/json",
    }
    handler.rfile = _RFile(payload_bytes)
    handler.wfile = wfile
    handler.requestline = f"{method} {path} HTTP/1.1"

    # Silence BaseHTTPRequestHandler's logging machinery in tests.
    handler.log_message = lambda *_args, **_kwargs: None  # type: ignore[assignment]
    handler.log_request = lambda *_args, **_kwargs: None  # type: ignore[assignment]
    handler.log_error = lambda *_args, **_kwargs: None  # type: ignore[assignment]
    return handler, wfile


def _parse_response(wfile: _WFile) -> tuple[int, dict]:
    """Parse the raw HTTP response captured by ``_WFile`` into (status, json)."""
    raw = wfile.body
    head, _, body = raw.partition(b"\r\n\r\n")
    status_line = head.split(b"\r\n", 1)[0].decode("latin-1")
    status = int(status_line.split(" ", 2)[1])
    return status, json.loads(body.decode("utf-8"))


class DiscoverWebEndpointTests(unittest.TestCase):
    def test_run_discover_from_request_returns_config_error(self) -> None:
        """No config + no example => JSON-shaped error, no exception."""
        with tempfile.TemporaryDirectory() as tmp:
            payload = {"config_path": str(Path(tmp) / "no-such.yaml")}
            result = run_discover_from_request(Path(tmp) / "output", payload)
        self.assertEqual(result.get("status"), "config_error")
        self.assertIn("Config file not found", result.get("message", ""))

    def test_discover_status_payload_when_no_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            from workspace_web import service as _svc

            original = _svc._resolve_discovery_log_dir
            _svc._resolve_discovery_log_dir = lambda: Path(tmp) / "no-such-dir"
            try:
                result = discover_status_payload(Path(tmp))
            finally:
                _svc._resolve_discovery_log_dir = original
        self.assertFalse(result["has_run"])
        self.assertIn("log_dir", result)

    def test_run_endpoint_returns_job_id(self) -> None:
        handler, wfile = _make_handler("POST", "/api/discover/run", {})
        try:
            handler.do_POST()
        except Exception as exc:  # noqa: BLE001
            self.fail(f"do_POST raised: {exc}")
        status, body = _parse_response(wfile)
        self.assertEqual(status, 200)
        # Async endpoint returns a job_id immediately.
        self.assertIn("job_id", body)
        self.assertEqual(body["status"], "running")

    def test_status_endpoint_returns_json(self) -> None:
        handler, wfile = _make_handler("GET", "/api/discover/status")
        try:
            handler.do_GET()
        except Exception as exc:  # noqa: BLE001
            self.fail(f"do_GET raised: {exc}")
        status, body = _parse_response(wfile)
        self.assertEqual(status, 200)
        self.assertIn("has_run", body)

    def test_run_endpoint_async_returns_job_id(self) -> None:
        """Async mode (default) returns immediately with a job_id."""
        from workspace_web.service import start_discover_job, _JOBS

        # Use ?sync= is NOT set, so async path; payload must be valid.
        # We point at a non-existent config to trigger fast config_error.
        handler, wfile = _make_handler(
            "POST",
            "/api/discover/run",
            {"config_path": "/nonexistent/discovery.yaml"},
        )
        handler.do_POST()
        status, body = _parse_response(wfile)
        self.assertEqual(status, 200)
        # Async path returns job_id; the thread will fail-fast on config error.
        self.assertIn("job_id", body)
        self.assertEqual(body["status"], "running")

        # Wait for the background thread to finish so the job record is populated.
        import time
        for _ in range(50):
            record = next(iter(_JOBS.values()), None)
            if record and record.get("status") != "running":
                break
            time.sleep(0.05)
        self.assertTrue(record is not None)
        self.assertNotEqual(record["status"], "running")

    def test_run_endpoint_sync_runs_inline(self) -> None:
        """sync=1 returns the full report instead of a job_id."""
        handler, wfile = _make_handler(
            "POST",
            "/api/discover/run?sync=1",
            {"config_path": "/nonexistent/discovery.yaml"},
        )
        handler.do_POST()
        status, body = _parse_response(wfile)
        self.assertEqual(status, 200)
        # Sync path returns config_error immediately, no job_id.
        self.assertNotIn("job_id", body)
        self.assertEqual(body["status"], "config_error")

    def test_job_endpoint_unknown_id(self) -> None:
        handler, wfile = _make_handler("GET", "/api/discover/job?id=nonexistent")
        handler.do_GET()
        status, body = _parse_response(wfile)
        self.assertEqual(status, 404)
        self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()