from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ai_intel_station.discovery import (
    DiscoveryLogger,
    latest_log_path,
    read_log_summary,
    recent_log_paths,
)


class DiscoveryLogTests(unittest.TestCase):
    def test_recent_log_paths_returns_empty_when_no_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "missing"
            self.assertEqual(recent_log_paths(log_dir, limit=5), [])
            # Missing dir handled gracefully.
            self.assertEqual(recent_log_paths(Path(tmp), limit=0), [])

    def test_recent_log_paths_respects_limit_and_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            import os
            import time

            for i, name in enumerate(["2026-01-01T00-00-00.log", "2026-02-01T00-00-00.log", "2026-03-01T00-00-00.log"]):
                p = log_dir / name
                p.write_text(f"run {i}", encoding="utf-8")
                os.utime(p, (1000 + i, 1000 + i))
                time.sleep(0.01)

            recent = recent_log_paths(log_dir, limit=2)
            self.assertEqual(len(recent), 2)
            # Newest first.
            self.assertEqual(recent[0].name, "2026-03-01T00-00-00.log")
            self.assertEqual(recent[1].name, "2026-02-01T00-00-00.log")

    def test_latest_log_path_returns_none_when_dir_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(latest_log_path(Path(tmp) / "nope"))

    def test_latest_log_path_picks_most_recent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            older = log_dir / "2026-01-01T00-00-00.log"
            older.write_text("old", encoding="utf-8")
            # Make sure mtimes differ deterministically.
            import os
            import time

            time.sleep(0.05)
            newer = log_dir / "2026-06-01T00-00-00.log"
            newer.write_text("new", encoding="utf-8")
            os.utime(older, (1000, 1000))
            os.utime(newer, (2000, 2000))
            self.assertEqual(latest_log_path(log_dir), newer)

    def test_read_log_summary_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            info = read_log_summary(Path(tmp) / "missing.log")
            self.assertFalse(info["exists"])
            self.assertIsNone(info["summary"])

    def test_read_log_summary_extracts_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "fake.log"
            log.write_text(
                "\n".join(
                    [
                        "=== discovery sweep ===",
                        "📊 Summary: succeeded=3 skipped=0 failed=1",
                        '   "started_at": "2026-06-28T23:00:00",',
                        '   "finished_at": "2026-06-28T23:00:05",',
                        "📰 Briefing: /tmp/briefing.md (5 items)",
                    ]
                ),
                encoding="utf-8",
            )
            info = read_log_summary(log)
            self.assertTrue(info["exists"])
            self.assertEqual(info["summary"], "succeeded=3 skipped=0 failed=1")
            self.assertEqual(info["started_at"], "2026-06-28T23:00:00")
            self.assertEqual(info["finished_at"], "2026-06-28T23:00:05")
            self.assertIn("/tmp/briefing.md", info["briefing"])
            self.assertIn("5 items", info["briefing"])

    def test_discovery_logger_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with DiscoveryLogger(Path(tmp)) as logger:
                logger.log("hello")
                logger.log("world")
            info = read_log_summary(logger.path)
            self.assertTrue(info["exists"])
            contents = logger.path.read_text(encoding="utf-8")
            self.assertIn("hello", contents)
            self.assertIn("world", contents)
            # Filename matches the timestamp pattern we promise in docs.
            self.assertRegex(logger.path.name, r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.log")

    def test_discovery_logger_prunes_old_logs(self) -> None:
        """When max_log_files is exceeded, oldest entries are deleted."""
        import os
        import time

        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            # Pre-seed 5 fake logs with deterministic mtimes.
            for i, name in enumerate(
                ["2026-01-01T00-00-00.log", "2026-02-01T00-00-00.log", "2026-03-01T00-00-00.log",
                 "2026-04-01T00-00-00.log", "2026-05-01T00-00-00.log"]
            ):
                p = log_dir / name
                p.write_text(f"old run {i}", encoding="utf-8")
                os.utime(p, (1000 + i, 1000 + i))
                time.sleep(0.005)

            # Limit = 3 means: keep newest 2, this run becomes #3.
            with DiscoveryLogger(log_dir, max_log_files=3) as logger:
                logger.log("fresh")

            remaining = sorted(p.name for p in log_dir.glob("*.log"))
            self.assertEqual(len(remaining), 3)
            # The two oldest must be gone; the two newest plus the fresh one remain.
            self.assertNotIn("2026-01-01T00-00-00.log", remaining)
            self.assertNotIn("2026-02-01T00-00-00.log", remaining)
            self.assertIn("2026-04-01T00-00-00.log", remaining)
            self.assertIn("2026-05-01T00-00-00.log", remaining)
            # The just-written one is the newest by mtime.
            self.assertIn(logger.path.name, remaining)

    def test_discovery_logger_zero_limit_keeps_all(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp)
            for name in ["a.log", "b.log", "c.log"]:
                (log_dir / name).write_text(name, encoding="utf-8")
            with DiscoveryLogger(log_dir, max_log_files=0) as logger:
                logger.log("x")
            self.assertEqual(len(list(log_dir.glob("*.log"))), 4)


if __name__ == "__main__":
    unittest.main()