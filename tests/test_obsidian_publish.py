"""Edge-case unit tests for `publish.obsidian.write_markdown` and `slugify`.

These tests pin down the contract around atomic writes (so a partial
write never produces a corrupted file the user thinks is valid) and
sanitisation (so a malicious `..` in the briefing title cannot escape
``output_root/``).
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from publish.obsidian import briefing_output_path, slugify, write_markdown


class SlugifyTests(unittest.TestCase):
    def test_simple_words(self) -> None:
        self.assertEqual(slugify("Hello World"), "hello-world")

    def test_empty_and_whitespace_fall_back(self) -> None:
        # Both must surface as the same non-empty placeholder so the
        # briefing path always has a filename.
        self.assertEqual(slugify(""), "briefing")
        self.assertEqual(slugify("   "), "briefing")

    def test_path_traversal_does_not_escape(self) -> None:
        # ../../etc/passwd would otherwise let a user-controlled title
        # overwrite arbitrary files under output_root — slugify must
        # turn every '.' and '/' into '-'.
        self.assertNotIn("/", slugify("../../etc/passwd"))
        self.assertNotIn("..", slugify("../../etc/passwd"))

    def test_unicode_preserved(self) -> None:
        # CJK characters fall inside the U+4E00-U+9FFF range, so they
        # should pass through slugify. (Without the CJK character class
        # the original regex stripped them.)
        self.assertIn("中文", slugify("中文 Agent Harness"))


class WriteMarkdownTests(unittest.TestCase):
    """The atomic-write contract."""

    def test_writes_final_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            write_markdown(path, "hello world")
            self.assertEqual(path.read_text(encoding="utf-8"), "hello world\n")

    def test_no_partial_file_when_overwrite(self) -> None:
        # After write_markdown, the existing file path is the new
        # content — never a half-written intermediate. fsync+rename is
        # the structural way to guarantee this; we check by reading
        # the file before/after.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            path.write_text("old content that is longer than new", encoding="utf-8")
            write_markdown(path, "tiny")
            self.assertEqual(path.read_text(encoding="utf-8"), "tiny\n")

    def test_leaves_no_temp_files_on_success(self) -> None:
        # mkstemp produces a sibling .tmp file. After successful
        # os.replace, that temp file must be gone.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            write_markdown(path, "hi")
            temps = [p for p in Path(tmp).iterdir() if p.name != "out.md"]
            self.assertEqual(temps, [], f"unexpected temp files left: {temps}")

    def test_trailing_newline_normalized(self) -> None:
        # The previous implementation stripped all trailing whitespace
        # and forced one final newline. Lock that down so future
        # refactors don't regress to leaving files with no newline.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            write_markdown(path, "first\n\n\n\n")
            self.assertTrue(path.read_text(encoding="utf-8").endswith("\n"))
            self.assertFalse(path.read_text(encoding="utf-8").endswith("\n\n\n"))


class BriefingOutputPathTests(unittest.TestCase):
    def test_path_inside_output_root(self) -> None:
        # briefing_output_path must always live under output_root —
        # never above it, even when title has odd characters.
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            path = briefing_output_path(output_root, "digests", "../../escape")
            self.assertTrue(
                path.resolve().is_relative_to(output_root.resolve()),
                f"briefing_output_path escaped {output_root}: {path}",
            )


if __name__ == "__main__":
    unittest.main()
