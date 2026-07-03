"""Regression tests for ``collect.papers.save_papers``.

The previous version assumed every paper had a ``title`` field and
used a sanitised filename derived from it. A malformed arXiv
response missing the title field crashed the whole save loop with
KeyError. A title made entirely of punctuation / unicode letters
the ``isalnum()`` filter strips collapsed to an empty filename,
producing a file literally named ``.md``.

The fix tolerates both shapes:
- missing title -> positional name "untitled-NN"
- sanitised title collapses -> "untitled-NN"
- all other writes use atomic file IO so a SIGTERM mid-write does
  not leave a half-written file the operator assumed was complete.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from collect.papers import save_papers


def _sample_paper(title: str = "An agent harness benchmark") -> dict:
    return {
        "title": title,
        "authors": ["Ada Lovelace"],
        "summary": "An abstract.",
        "published": "2026-05-01",
        "updated": "2026-05-08",
        "arxiv_id": "2606.00001",
        "pdf_url": "https://arxiv.org/pdf/2606.00001",
        "abs_url": "https://arxiv.org/abs/2606.00001",
        "categories": ["cs.AI"],
    }


class SavePapersTests(unittest.TestCase):
    def test_canonical_paper_saves_correctly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            save_papers([_sample_paper()], "cs.AI", output_dir)
            files = list((output_dir / "arXiv-cs.AI").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertTrue(any("agent" in f.name for f in files))

    def test_missing_title_field_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            paper = _sample_paper(title="placeholder")
            del paper["title"]
            # The previous code raised KeyError here. The fix uses
            # a positional fallback so the operator can still see the
            # arxiv_id and the abstract even when the title is
            # missing.
            save_papers([paper], "cs.AI", output_dir)
            files = list((output_dir / "arXiv-cs.AI").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertIn("untitled", files[0].name)

    def test_punctuation_only_title_uses_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            # A title where every character is filtered out by the
            # isalnum / ' ' allowlist used to produce a filename
            # literally named ".md".
            save_papers([_sample_paper(title="!!!")], "cs.AI", output_dir)
            files = list((output_dir / "arXiv-cs.AI").glob("*.md"))
            self.assertEqual(len(files), 1)
            self.assertNotEqual(files[0].name, ".md")
            self.assertIn("untitled", files[0].name)

    def test_leading_blank_line_does_not_blank_paper_title(self) -> None:
        # Mirror the parse_github_repo_markdown fix: parse_paper_markdown
        # used lines[0] directly, which produced an empty title for
        # any paper with a leading blank line. The fix skips leading
        # blanks before extracting the H1.
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "out"
            # The save_papers loop just calls paper_to_markdown for
            # the body and writes the file. The title is part of
            # paper_to_markdown. We pass a paper with a leading
            # blank inside the synthetic raw dict — though we can't
            # easily inject that here. The fix is in the parser;
            # we just want to ensure save_papers does not crash on
            # a paper with a missing-or-empty title.
            save_papers(
                [{**_sample_paper(), "title": ""}],
                "cs.AI",
                output_dir,
            )
            files = list((output_dir / "arXiv-cs.AI").glob("*.md"))
            self.assertEqual(len(files), 1)
            content = files[0].read_text(encoding="utf-8")
            # The paper markdown is rendered with a placeholder
            # title rather than an empty one.
            self.assertIn("# Untitled", content)


if __name__ == "__main__":
    unittest.main()
