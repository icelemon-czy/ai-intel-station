from __future__ import annotations

import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from workspace_web.discovery import (
    _BRIEFING_RE,
    _parse_briefing_marker,
    discover_status_payload,
)


class BriefingMarkerParserTests(unittest.TestCase):
    """Real tests for the briefing marker parser — previously the front-end
    was splitting strings to recover a path, which broke for any output
    outside the ``output/`` tree."""

    def test_parses_standard_marker(self) -> None:
        result = _parse_briefing_marker(
            "output/briefing/reading-lists/daily-2026-06-29.md (5 items)"
        )
        self.assertEqual(result, {
            "path": "briefing/reading-lists/daily-2026-06-29.md",
            "item_count": 5,
        })

    def test_parses_dry_run_marker(self) -> None:
        result = _parse_briefing_marker("(dry-run) (0 items)")
        self.assertEqual(result, {"path": "(dry-run)", "item_count": 0})

    def test_parses_signal_status_marker(self) -> None:
        result = _parse_briefing_marker(
            "output/briefing/signals/daily-2026-08-13.md (3 items, status=partial)"
        )
        self.assertEqual(
            result,
            {
                "path": "briefing/signals/daily-2026-08-13.md",
                "item_count": 3,
                "status": "partial",
            },
        )

    def test_parses_failed_marker_without_clickable_path(self) -> None:
        self.assertEqual(
            _parse_briefing_marker("None (0 items, status=failed)"),
            {"path": None, "item_count": 0, "status": "failed"},
        )

    def test_returns_none_for_empty(self) -> None:
        self.assertIsNone(_parse_briefing_marker(None))
        self.assertIsNone(_parse_briefing_marker(""))

    def test_returns_none_for_unparseable(self) -> None:
        # Garbage input shouldn't raise; it returns None so the UI falls back
        # to a "no briefing" message instead of crashing.
        self.assertIsNone(_parse_briefing_marker("not a real marker"))
        self.assertIsNone(_parse_briefing_marker("foo.md (missing count)"))

    def test_parses_path_outside_output(self) -> None:
        """A path not under output/ stays as-is (no leading-stripping)."""
        result = _parse_briefing_marker("/tmp/briefing.md (3 items)")
        self.assertEqual(result, {"path": "/tmp/briefing.md", "item_count": 3})

    def test_regex_matches_typical_markers(self) -> None:
        cases = [
            ("a.md (1 item)", "a.md", "1"),
            ("x/y/z.md (42 items)", "x/y/z.md", "42"),
            ("(dry-run) (0 items)", "(dry-run)", "0"),
            ("signals.md (2 items, status=ready)", "signals.md", "2"),
        ]
        for text, expected_path, expected_count in cases:
            with self.subTest(text=text):
                match = _BRIEFING_RE.match(text)
                self.assertIsNotNone(match)
                self.assertEqual(match.group("path"), expected_path)
                self.assertEqual(match.group("count"), expected_count)


class DiscoverStatusPayloadTests(unittest.TestCase):
    """The web status endpoint now returns structured briefing instead of a
    free-text marker string — verify that end-to-end."""

    def test_status_payload_includes_structured_briefing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            log_dir.mkdir()
            ts = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
            (log_dir / f"{ts}.log").write_text(
                "\n".join([
                    "=== discovery sweep ===",
                    "📊 Summary: succeeded=3 skipped=0 failed=0",
                    '   "started_at": "2026-06-29T10:00:00",',
                    '   "finished_at": "2026-06-29T10:00:01",',
                    "📰 Briefing: output/briefing/reading-lists/daily-2026-06-29.md (3 items)",
                ]),
                encoding="utf-8",
            )

            # Bypass the resolver to point at our isolated log dir.
            from workspace_web import discovery as _svc

            original = _svc._resolve_discovery_log_dir
            _svc._resolve_discovery_log_dir = lambda: log_dir
            try:
                payload = discover_status_payload(Path(tmp))
            finally:
                _svc._resolve_discovery_log_dir = original

        self.assertTrue(payload["has_run"])
        self.assertEqual(payload["briefing"]["path"], "briefing/reading-lists/daily-2026-06-29.md")
        self.assertEqual(payload["briefing"]["item_count"], 3)
        # Legacy text marker is no longer shipped to the front-end.
        self.assertNotIsInstance(payload["briefing"], str)

    def test_status_payload_exposes_signal_outcome(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            log_dir.mkdir()
            (log_dir / "2026-08-13T10-00-00.log").write_text(
                "\n".join(
                    [
                        "📊 Summary: succeeded=2 skipped=0 failed=1",
                        "📰 Briefing: output/briefing/signals/daily.md (2 items, status=partial)",
                        '  "status": "partial"',
                    ]
                ),
                encoding="utf-8",
            )
            from workspace_web import discovery as _svc

            original = _svc._resolve_discovery_log_dir
            _svc._resolve_discovery_log_dir = lambda: log_dir
            try:
                payload = discover_status_payload(Path(tmp))
            finally:
                _svc._resolve_discovery_log_dir = original

        self.assertEqual(payload["briefing_status"], "partial")
        self.assertEqual(payload["briefing"]["status"], "partial")


if __name__ == "__main__":
    unittest.main()
