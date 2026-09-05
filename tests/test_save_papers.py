"""Regression tests for ``collect.papers.save_papers``.

Papers are now stored at a stable source identity (``<arxiv-id>.md`` under the
papers root) instead of a legacy per-category directory keyed by a positional
index and a title slug. These tests assert:

- canonical paper -> ``<arxiv-id>.md`` next to ``<arxiv-id>.research-item.json``
- missing / empty / punctuation-only title -> no crash, ``# Untitled`` placeholder,
  and the file is still named by the arxiv id (never a bare ``.md``)
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from collect.papers import save_papers

_SAMPLE_ID = "2606.00001"


def _sample_paper(title: str = "An agent harness benchmark") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "summary": "An abstract.",
        "published": "2026-05-01",
        "updated": "2026-05-08",
        "arxiv_id": _SAMPLE_ID,
        "pdf_url": f"https://arxiv.org/pdf/{_SAMPLE_ID}",
        "abs_url": f"https://arxiv.org/abs/{_SAMPLE_ID}",
        "categories": ["cs.AI"],
    }


class SavePapersTests(unittest.TestCase):
    def test_canonical_paper_saves_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            save_papers([_sample_paper()], "cs.AI", output_dir)
            self.assertTrue((output_dir / f"{_SAMPLE_ID}.md").is_file())
            self.assertTrue((output_dir / f"{_SAMPLE_ID}.research-item.json").is_file())
            self.assertNotIn("arXiv-cs.AI", output_dir.as_posix())

    def test_missing_title_field_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            paper = _sample_paper(title="placeholder")
            del paper["title"]
            # The previous code raised KeyError here. A missing title now still
            # yields a placeholder body, named by the stable arxiv id.
            save_papers([paper], "cs.AI", output_dir)
            md = output_dir / f"{_SAMPLE_ID}.md"
            self.assertTrue(md.is_file())
            self.assertIn("# Untitled", md.read_text(encoding="utf-8"))

    def test_punctuation_only_title_is_still_identifiable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            # The legacy layout used the title to build the filename, so a
            # punctuation-only title could produce a bare ``.md``. The identity
            # layout is title-independent, so the filename stays the arxiv id.
            save_papers([_sample_paper(title="!!!")], "cs.AI", output_dir)
            md = output_dir / f"{_SAMPLE_ID}.md"
            self.assertTrue(md.is_file())
            self.assertNotEqual(md.name, ".md")

    def test_empty_title_renders_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            save_papers([{**_sample_paper(), "title": ""}], "cs.AI", output_dir)
            md = output_dir / f"{_SAMPLE_ID}.md"
            self.assertTrue(md.is_file())
            self.assertIn("# Untitled", md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
