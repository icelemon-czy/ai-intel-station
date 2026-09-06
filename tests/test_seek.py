"""Contract tests for Interest Sweep (`research seek`).

`collect/seek.py` owns the per-source sweep + persist and the per-source
report; the CLI layer (`cli/commands.py`) owns composing the this-run
reading list via `briefing.service`.
"""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai_intel_station.cli.commands import run_seek_command, save_seek_reading_list
from ai_intel_station.collect.seek import run_seek
from ai_intel_station.library.items import ResearchItem, write_research_item

REPO_URL = "https://github.com/ex/harness"
ABS_URL = "https://arxiv.org/abs/2606.00001"


def _repo() -> dict:
    return {
        "name": "harness",
        "url": REPO_URL,
        "owner": {"login": "ex"},
        "description": "agent harness",
        "stargazersCount": 1,
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-01-02T00:00:00Z",
    }


def _paper() -> dict:
    return {
        "title": "An agent harness benchmark",
        "authors": ["Ada Lovelace"],
        "summary": "An abstract.",
        "published": "2026-05-01",
        "updated": "2026-05-08",
        "arxiv_id": "2606.00001",
        "pdf_url": "https://arxiv.org/pdf/2606.00001",
        "abs_url": ABS_URL,
        "categories": ["cs.AI"],
    }


class SeekTests(unittest.TestCase):
    def test_dry_run_does_not_fetch_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch("ai_intel_station.collect.seek.github.run_gh") as run_gh,
                patch("ai_intel_station.collect.seek.papers.fetch_papers_by_query") as fetch,
                patch("ai_intel_station.collect.seek.hackernews.collect_topic") as hn,
            ):
                result = run_seek("agent memory", output, dry_run=True)
            self.assertTrue(result.dry_run)
            self.assertIn("dry-run", result.message)
            self.assertIn("GitHub", result.message)
            self.assertIn("arXiv", result.message)
            run_gh.assert_not_called()
            fetch.assert_not_called()
            hn.assert_not_called()
            self.assertEqual(list(output.iterdir()), [])

    def test_run_seek_persists_archive_but_never_writes_briefing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch(
                    "ai_intel_station.collect.seek.github.run_gh",
                    return_value=json.dumps([_repo()]),
                ),
                patch(
                    "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                    return_value=[_paper()],
                ),
                patch(
                    "ai_intel_station.collect.seek.hackernews.collect_topic",
                    return_value=([], []),
                ),
            ):
                result = run_seek("agent harness", output)
            self.assertGreaterEqual(len(result.new_items), 2)
            self.assertTrue(any(output.joinpath("github").rglob("*.md")))
            self.assertTrue((output / "papers" / "2606.00001.research-item.json").is_file())
            # Briefing is the CLI layer's job; collect never generates it.
            self.assertIsNone(result.briefing_path)
            self.assertFalse((output / "briefing").exists())
            self.assertIn("briefing: skipped", result.message)

    def test_existing_url_is_skip_not_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            sidecar_dir = output / "github" / "ex" / "harness"
            sidecar_dir.mkdir(parents=True)
            write_research_item(
                ResearchItem(
                    source="github",
                    item_type="repository",
                    title="harness",
                    canonical_url=REPO_URL,
                ),
                sidecar_dir / "research-item.json",
            )
            with (
                patch(
                    "ai_intel_station.collect.seek.github.run_gh",
                    return_value=json.dumps([_repo()]),
                ) as run_gh,
                patch(
                    "ai_intel_station.collect.seek.github.save_search_results"
                ) as save,
                patch(
                    "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                    return_value=[],
                ),
                patch(
                    "ai_intel_station.collect.seek.hackernews.collect_topic",
                    return_value=([], []),
                ),
            ):
                result = run_seek("agent harness", output)
            run_gh.assert_called_once()
            save.assert_not_called()
            self.assertEqual(len(result.new_items), 0)
            self.assertEqual(len(result.existing_items), 1)
            self.assertEqual(result.existing_items[0].canonical_url, REPO_URL)
            # The skip is reported on the matching per-source line.
            self.assertIn("github: 0 succeeded, 1 skipped", result.message)

    def test_github_failure_does_not_block_papers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch(
                    "ai_intel_station.collect.seek.github.run_gh",
                    side_effect=RuntimeError("gh down"),
                ),
                patch(
                    "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                    return_value=[_paper()],
                ),
                patch(
                    "ai_intel_station.collect.seek.hackernews.collect_topic",
                    return_value=([], []),
                ),
            ):
                result = run_seek("agent harness", output)
            self.assertIn("github", result.failures)
            self.assertTrue((output / "papers" / "2606.00001.research-item.json").is_file())
            self.assertTrue(any(item.source == "papers" for item in result.new_items))
            # Per-source report: the failed source is named, the survivor still
            # reports its success count.
            self.assertIn("github: failed", result.message)
            self.assertIn("papers: 1 succeeded", result.message)

    def test_empty_topic_and_bad_limit_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with self.assertRaises(ValueError):
                run_seek("  ", output)
            with self.assertRaises(ValueError):
                run_seek("topic", output, limit=0)


class SeekReadingListTests(unittest.TestCase):
    """The CLI layer composes the this-run reading list from sweep hits."""

    def _run(self, output: Path, *, no_briefing: bool = False) -> tuple[int, str]:
        """Run the seek command with github yielding a NEW repo and papers an
        existing paper already in the Library, so both memberships appear."""
        stdout = io.StringIO()
        with (
            patch(
                "ai_intel_station.collect.seek.github.run_gh",
                return_value=json.dumps([_repo()]),
            ),
            patch(
                "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                return_value=[_paper()],
            ),
            patch(
                "ai_intel_station.collect.seek.hackernews.collect_topic",
                return_value=([], []),
            ),
            contextlib.redirect_stdout(stdout),
        ):
            code = run_seek_command(
                "agent harness", output, dry_run=False, no_briefing=no_briefing, limit=10
            )
        return code, stdout.getvalue()

    def _seed_existing_paper(self, output: Path) -> None:
        sidecar_dir = output / "papers" / "2606.00001"
        sidecar_dir.mkdir(parents=True)
        write_research_item(
            ResearchItem(
                source="papers",
                item_type="paper",
                title="An agent harness benchmark",
                canonical_url=ABS_URL,
            ),
            sidecar_dir / "research-item.json",
        )

    def test_default_writes_reading_list_with_new_and_existing_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            self._seed_existing_paper(output)
            code, stdout = self._run(output)
            self.assertEqual(code, 0)
            files = list((output / "briefing" / "reading-lists").glob("*.md"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            # Membership contract: newly collected AND already-in-library hits.
            self.assertIn(REPO_URL, content)
            self.assertIn(ABS_URL, content)
            self.assertIn("briefing:", stdout)
            self.assertIn(files[0].name, stdout)

    def test_no_briefing_writes_nothing_under_briefing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            code, stdout = self._run(output, no_briefing=True)
            self.assertEqual(code, 0)
            self.assertFalse((output / "briefing").exists())
            self.assertIn("briefing: skipped", stdout)

    def test_helper_skips_zero_hit_sweep(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch("ai_intel_station.collect.seek.github.run_gh", return_value="[]"),
                patch(
                    "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                    return_value=[],
                ),
                patch(
                    "ai_intel_station.collect.seek.hackernews.collect_topic",
                    return_value=([], []),
                ),
            ):
                result = run_seek("agent harness", output)
                save_seek_reading_list(result, output)
            self.assertEqual(result.new_items, [])
            self.assertEqual(result.existing_items, [])
            self.assertIsNone(result.briefing_path)
            self.assertFalse((output / "briefing").exists())

    def test_helper_not_called_leaves_no_briefing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            with (
                patch(
                    "ai_intel_station.collect.seek.github.run_gh",
                    return_value=json.dumps([_repo()]),
                ),
                patch(
                    "ai_intel_station.collect.seek.papers.fetch_papers_by_query",
                    return_value=[],
                ),
                patch(
                    "ai_intel_station.collect.seek.hackernews.collect_topic",
                    return_value=([], []),
                ),
            ):
                result = run_seek("agent harness", output)
            self.assertGreater(len(result.new_items), 0)
            self.assertFalse((output / "briefing").exists())


if __name__ == "__main__":
    unittest.main()
