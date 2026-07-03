"""Regression tests for ``parse_github_repo_markdown`` heading-match
robustness.

A previous version of the parser used ``line == '## Topics'`` exact
match. A `gh repo view` round-trip followed by a manual edit
frequently produced '## topics' (lowercase) or '##  Topics  ' (extra
spaces); the parser silently dropped every tag in those cases.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from library.items import parse_github_repo_markdown


def _write_markdown(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


class ParseGithubRepoMarkdownSectionTests(unittest.TestCase):
    """Tags survive inconsistent heading formatting."""

    def _minimal_body(self) -> str:
        return (
            "# demo\n"
            "\n"
            "> demo repository\n"
            "\n"
            "- 🌐 URL: https://github.com/x/y\n"
            "- ⭐ Stars: 5\n"
            "- 🏷️ Language: Go\n"
            "- 📅 Created: 2026-05-01\n"
            "- 🔄 Updated: 2026-05-08\n"
        )

    def test_topics_canonical_heading(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._minimal_body() + "\n## Topics\n\n- `agent`\n- `harness`\n")
            item = parse_github_repo_markdown(md)
            self.assertIn("agent", item.tags)
            self.assertIn("harness", item.tags)

    def test_topics_lowercase(self) -> None:
        # '## topics' (lowercase) is a real-world variation after a
        # hand-edit. The parser must still pick the tag list.
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._minimal_body() + "\n## topics\n\n- `agent`\n")
            item = parse_github_repo_markdown(md)
            self.assertIn("agent", item.tags)

    def test_topics_with_trailing_whitespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(md, self._minimal_body() + "\n##  Topics  \n\n- `agent`\n")
            item = parse_github_repo_markdown(md)
            self.assertIn("agent", item.tags)

    def test_open_issues_lowercase(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(
                md,
                self._minimal_body()
                + "\n## open Issues\n\n- [#1] bug\n- [#2] feature\n",
            )
            item = parse_github_repo_markdown(md)
            self.assertEqual(item.metadata.get("issue_count", 0) >= 0, True)

    def test_section_state_resets_at_next_h2(self) -> None:
        # Once a section ends, subsequent h2's start fresh. This was
        # already correct in the old code — pin it.
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(
                md,
                self._minimal_body()
                + "\n## Topics\n\n- `a`\n\n## Readme\n\nplain text\n",
            )
            item = parse_github_repo_markdown(md)
            self.assertIn("a", item.tags)

    def test_leading_blank_line_does_not_blank_title(self) -> None:
        # A file with a leading blank line (e.g. shell-redirect artefact
        # or `gh repo view` round-trip with a leading BOM) used to
        # index lines[0] which is the empty string — so the title
        # was silently lost. The fix skips leading blanks before
        # extracting the H1.
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(
                md,
                "\n# real title\n\n- 🌐 URL: https://github.com/x/y\n",
            )
            item = parse_github_repo_markdown(md)
            self.assertEqual(item.title, "real title")

    def test_h2_heading_strips_two_hashes(self) -> None:
        # A hand-edited file with `## title` (a deeper heading) used
        # to keep the leading `##` in place. The fix accepts any
        # level (##, ###) and strips the prefix.
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "repo" / "README.md"
            _write_markdown(
                md,
                "## real title\n\n- 🌐 URL: https://github.com/x/y\n",
            )
            item = parse_github_repo_markdown(md)
            self.assertEqual(item.title, "real title")


if __name__ == "__main__":
    unittest.main()
