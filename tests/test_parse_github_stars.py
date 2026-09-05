"""Regression test for parse_github_repo_markdown — non-numeric Stars line.

The previous version called ``int(line.removeprefix("- ⭐ Stars: ").strip())``
without a try/except. A hand-edited markdown with ``- ⭐ Stars: n/a``
crashed the whole parser mid-loop, dropping every tag the file
declared. Now the failure is contained.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from library.backfill import parse_github_repo_markdown


def _write_markdown(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class ParseGithubRepoMarkdownStarsTests(unittest.TestCase):
    def _body(self, stars_line: str = "- ⭐ Stars: 42") -> str:
        return (
            "# demo\n"
            "\n"
            "> demo repository\n"
            "\n"
            f"{stars_line}\n"
            "- 🏷️ Language: Go\n"
            "- 🌐 URL: https://github.com/x/y\n"
            "- 📅 Created: 2026-05-01\n"
            "- 🔄 Updated: 2026-05-08\n"
            "\n"
            "## Topics\n\n"
            "- `agent`\n"
        )

    def test_numeric_stars_parses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._body("- ⭐ Stars: 42"))
            item = parse_github_repo_markdown(md)
            # Tag list should be parsed even when stars is valid.
            self.assertIn("agent", item.tags)

    def test_non_numeric_stars_does_not_crash(self) -> None:
        # A hand-edited 'n/a' used to raise ValueError mid-loop. The
        # parser now tolerates the value and still parses the rest of
        # the file.
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._body("- ⭐ Stars: n/a"))
            item = parse_github_repo_markdown(md)
            self.assertIn("agent", item.tags)

    def test_empty_stars_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._body("- ⭐ Stars: "))
            item = parse_github_repo_markdown(md)
            self.assertIn("agent", item.tags)


if __name__ == "__main__":
    unittest.main()
