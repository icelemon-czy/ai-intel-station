"""Edge-case unit tests for the library + workspace-job fixes.

Two regressions we want to lock down:
  1. ``load_research_items`` must not abort the whole library load when
     a single sidecar is corrupt (truncated mid-write).
  2. The in-memory job registry must not grow without bound — finished
     jobs past ``MAX_JOBS`` get evicted so long-running servers stay
     snappy.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from library.items import ResearchItem, write_research_item
from library.storage import load_research_items
from workspace_web import service


class LoadResearchItemsResilienceTests(unittest.TestCase):
    def _seed_two_items(self, root: Path) -> tuple[ResearchItem, ResearchItem]:
        good = ResearchItem(
            source="github",
            item_type="repo",
            title="good",
            canonical_url="https://github.com/x/good",
            summary="ok",
            authors=[],
            published_at="2026-05-01",
            tags=[],
            output_path="output/github/good/README.md",
        )
        other = ResearchItem(
            source="papers",
            item_type="paper",
            title="other",
            canonical_url="https://arxiv.org/abs/0000.00000",
            summary="paper",
            authors=["x"],
            published_at="2026-05-01",
            tags=[],
            output_path="output/papers/other/other.md",
        )
        write_research_item(good, root / "github" / "good" / "research-item.json")
        write_research_item(other, root / "papers" / "other" / "research-item.json")
        return good, other

    def test_one_corrupt_sidecar_does_not_abort_whole_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            good, other = self._seed_two_items(output_root)
            # Truncate the github sidecar to half its JSON body so it
            # is unrecoverable. Reading both sidecars used to abort.
            corrupt = output_root / "github" / "good" / "research-item.json"
            bad_content = corrupt.read_text(encoding="utf-8")
            corrupt.write_text(bad_content[: len(bad_content) // 2], encoding="utf-8")

            # Both items should still appear — the corrupt one is skipped
            # with a warning, the other loads fine.
            loaded = load_research_items(output_root)
            loaded_titles = {item.title for item in loaded if item.title in {"good", "other"}}
            self.assertEqual(loaded_titles, {"other"})

    def test_empty_corrupt_file_is_skipped_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            other = ResearchItem(
                source="papers",
                item_type="paper",
                title="other",
                canonical_url="https://arxiv.org/abs/0000.00000",
                summary="paper",
                authors=[],
                published_at="2026-05-01",
                tags=[],
                output_path="output/papers/other/other.md",
            )
            write_research_item(other, output_root / "papers" / "other" / "research-item.json")
            (output_root / "github" / "broken" / "research-item.json").parent.mkdir(parents=True)
            (output_root / "github" / "broken" / "research-item.json").write_text("", encoding="utf-8")
            loaded = load_research_items(output_root)
            self.assertTrue(any(item.title == "other" for item in loaded))


class JobRegistryEvictionTests(unittest.TestCase):
    """``service._JOBS`` must keep only the most-recent ``MAX_JOBS`` jobs."""

    def setUp(self) -> None:
        # Each test starts with a fresh registry so they are independent.
        service._JOBS.clear()

    def test_evict_caps_registry_to_max_jobs(self) -> None:
        from datetime import datetime, timedelta

        # Seed 50 finished jobs with timestamps spread over time so we
        # can order by started_at.
        now = datetime.now()
        with service._JOBS_LOCK:
            for i in range(50):
                service._JOBS[f"job-{i:03d}"] = {
                    "status": "success",
                    "started_at": (now + timedelta(seconds=i)).isoformat(timespec="seconds"),
                    "result": {"i": i},
                }
            service._evict_old_jobs()
        self.assertLessEqual(len(service._JOBS), service.MAX_JOBS)
        # The most recent MAX_JOBS entries (highest i) survive.
        surviving = sorted(service._JOBS.keys())
        # The evicted ones have the lowest indices.
        self.assertNotIn("job-000", surviving)

    def test_running_jobs_are_never_evicted(self) -> None:
        from datetime import datetime

        now_iso = datetime.now().isoformat(timespec="seconds")
        with service._JOBS_LOCK:
            for i in range(service.MAX_JOBS + 5):
                # Half running, half finished. Mark every other entry
                # as 'running' so it must never get evicted.
                service._JOBS[f"job-{i:03d}"] = {
                    "status": "running" if i % 2 == 0 else "success",
                    "started_at": now_iso,
                    "result": None,
                }
            service._evict_old_jobs()
        # The MAX_JOBS eviction must keep all 'running' entries.
        running_count = sum(1 for r in service._JOBS.values() if r.get("status") == "running")
        self.assertGreater(running_count, 0)


class GetJobReturnValueTests(unittest.TestCase):
    """The returned record must be a deep copy — mutating it must not
    corrupt the in-memory registry.
    """

    def setUp(self) -> None:
        service._JOBS.clear()

    def test_get_job_returns_independent_copy(self) -> None:
        service._JOBS["job-1"] = {
            "status": "success",
            "result": {"nested": {"deep": 1}},
            "started_at": "2026-01-01T00:00:00",
        }
        first = service.get_job("job-1")
        first["result"]["nested"]["deep"] = 999
        first["status"] = "mutated"

        second = service.get_job("job-1")
        self.assertEqual(second["status"], "success")
        self.assertEqual(second["result"]["nested"]["deep"], 1)


if __name__ == "__main__":
    unittest.main()
