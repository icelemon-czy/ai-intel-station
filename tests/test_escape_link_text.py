"""Regression tests for ``_escape_link_text`` hardening:

1. Multiline input collapses onto one line so the bullet stays a
   single bullet rather than splitting into siblings.
2. ``\\.`` backslash-period is escaped so an Obsidian extension
   directive inside a title does not break the link label.
3. Existing bracket-escape behaviour still holds.
"""
from __future__ import annotations

import unittest

from briefing.reports import _escape_link_text, _format_item
from library.items import ResearchItem


class EscapeLinkTextTests(unittest.TestCase):
    def test_escapes_closing_bracket(self) -> None:
        self.assertEqual(_escape_link_text("Python] beyond"), "Python\\] beyond")

    def test_leaves_text_alone_when_no_bracket(self) -> None:
        self.assertEqual(_escape_link_text("normal title"), "normal title")

    def test_collapses_newlines_to_spaces(self) -> None:
        # A title like 'foo\nbar' would otherwise break the bullet into
        # multiple rendered lines that Obsidian treats as siblings of
        # the parent bullet.
        self.assertEqual(_escape_link_text("foo\nbar"), "foo bar")
        self.assertEqual(_escape_link_text("a\r\nb"), "a  b")

    def test_escapes_backslash_period(self) -> None:
        # Obsidian/CommonMark parses `\\.` as an extension directive.
        # Inside a link label the marker should not fire.
        self.assertEqual(
            _escape_link_text("foo\\.bar"),
            "foo\\\\.bar",
        )

    def test_combined_brackets_and_newlines(self) -> None:
        # Real-world: a Jira-style title with a newline AND a literal
        # backslash-period sequence (which Obsidian/CommonMark parse
        # as an extension directive).
        out = _escape_link_text("foo]\n.\\bar")
        # Newlines must collapse so the bullet cannot split.
        self.assertNotIn("\n", out)
        # Bracket escape must be present so the link label closes
        # properly.
        self.assertIn("\\]", out)
        # Source `\\b` passes through as the markdown-correct form
        # (backslash is preserved).
        self.assertIn("bar", out)


class FormatItemMultilineTests(unittest.TestCase):
    """A title with newlines must not break the bullet wrapper."""

    def test_title_with_newline_is_single_bullet(self) -> None:
        item = ResearchItem(
            source="github",
            item_type="repo",
            title="foo\nbar",
            canonical_url="https://example.com/foo",
            summary="",
            authors=[],
            published_at="2026-05-01",
            tags=[],
            output_path="output/foo/README.md",
        )
        lines = _format_item(item, checked=False)
        joined = "\n".join(lines)
        # The bullet's title was collapsed; the embedded newline is
        # gone. Obsidian would otherwise split [- [foo\nbar](url) ]
        # across multiple lines and treat them as siblings.
        self.assertNotIn("[foo\n", joined)
        self.assertNotIn("foo\nbar", joined)
        self.assertIn("foo bar", joined)


if __name__ == "__main__":
    unittest.main()
