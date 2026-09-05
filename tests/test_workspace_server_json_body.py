"""Edge-case unit tests for `ai_intel_station.adapters.web.server._json_body`.

These tests catch regressions where the body parser either:
  - crashes with an uncaught ValueError on a malformed request, OR
  - silently swallows malformed input that should produce a 400 response.

A failing test here means the server would leak a 500 stack trace or
mishandle a real client POST.
"""
from __future__ import annotations

import io
import unittest

from ai_intel_station.adapters.web.server import _json_body


class _FakeHandler:
    def __init__(self, raw: bytes, content_length_header: str | None) -> None:
        self.headers: dict[str, str] = {}
        if content_length_header is not None:
            self.headers["Content-Length"] = content_length_header
        self.rfile = io.BytesIO(raw)


class JsonBodyParserTests(unittest.TestCase):
    def test_empty_body_returns_empty_dict(self) -> None:
        result = _json_body(_FakeHandler(b"", "0"))
        self.assertEqual(result, {})

    def test_absent_content_length_defaults_to_empty_body(self) -> None:
        # No Content-Length header at all — should not crash; should
        # behave like Content-Length: 0.
        result = _json_body(_FakeHandler(b"", None))
        self.assertEqual(result, {})

    def test_valid_json_payload_round_trips(self) -> None:
        payload = b'{"a":1, "b":[true]}'
        result = _json_body(_FakeHandler(payload, str(len(payload))))
        self.assertEqual(result, {"a": 1, "b": [True]})

    def test_non_utf8_body_raises_value_error(self) -> None:
        # 0xff is not valid utf-8 start byte.
        with self.assertRaises(ValueError) as ctx:
            _json_body(_FakeHandler(b"\xff\xfe\xfd", "3"))
        self.assertIn("utf-8", str(ctx.exception).lower())

    def test_invalid_json_raises_value_error_with_message(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            _json_body(_FakeHandler(b"not-json", "8"))
        # The dispatch layer formats this into a 400 response — we
        # require a real message so the React `requestJson` wrapper
        # can show something useful.
        self.assertIn("json", str(ctx.exception).lower())

    def test_negative_content_length_raises_value_error(self) -> None:
        # Without the guard, `handler.rfile.read(-1)` would block
        # reading until EOF — a slow-loris style denial of service.
        with self.assertRaises(ValueError) as ctx:
            _json_body(_FakeHandler(b"", "-1"))
        self.assertIn("negative", str(ctx.exception).lower())

    def test_non_numeric_content_length_raises_value_error(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            _json_body(_FakeHandler(b"", "abc"))
        self.assertIn("invalid content-length", str(ctx.exception).lower())


if __name__ == "__main__":
    unittest.main()
