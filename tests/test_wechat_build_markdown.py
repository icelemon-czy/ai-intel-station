"""Regression tests for ``build_markdown`` in collect.wechat.

The wechat body was previously inlined into the H1 heading without
any sanitisation. A title with an embedded newline or a missing
title would either split the H1 across two visual lines or raise
KeyError. The fix collapses newlines to a space and falls back to
'Untitled' when the title is missing entirely.
"""
from __future__ import annotations

import unittest

from collect.wechat import build_markdown


class BuildMarkdownTests(unittest.TestCase):
    def test_canonical_title(self) -> None:
        md = build_markdown(
            {"title": "hello"},
            "body line",
        )
        self.assertIn("# hello", md)
        self.assertIn("body line", md)

    def test_title_with_newline_collapses_to_space(self) -> None:
        # A two-line title must NOT render as two H1 headings or split
        # the heading across two visual lines.
        md = build_markdown(
            {"title": "foo\nbar"},
            "",
        )
        # The H1 line should not contain a newline.
        h1_line = next(line for line in md.split("\n") if line.startswith("#"))
        self.assertNotIn("\n", h1_line)
        self.assertIn("foo bar", h1_line)

    def test_title_with_carriage_return_collapsed(self) -> None:
        md = build_markdown(
            {"title": "foo\r\nbar"},
            "",
        )
        h1_line = next(line for line in md.split("\n") if line.startswith("#"))
        # Whitespace artefacts from CRLF should not appear in the H1.
        self.assertNotIn("foo\nbar", h1_line)
        self.assertIn("foo", h1_line)
        self.assertIn("bar", h1_line)

    def test_missing_title_falls_back_to_untitled(self) -> None:
        # The wechat page sometimes has no <h1> at all. A missing
        # title used to KeyError; the fix substitutes a sane default.
        md = build_markdown({"author": "Ada"}, "")
        self.assertIn("# Untitled", md)

    def test_empty_string_title_falls_back_to_untitled(self) -> None:
        md = build_markdown({"title": ""}, "")
        self.assertIn("# Untitled", md)

    def test_whitespace_only_title_falls_back_to_untitled(self) -> None:
        md = build_markdown({"title": "   \n\t"}, "")
        self.assertIn("# Untitled", md)

    def test_metadata_block_includes_only_present_fields(self) -> None:
        # The metadata block (between # and ---) must not include empty
        # lines for fields that are absent.
        md = build_markdown({"title": "x", "author": "Ada"}, "")
        self.assertIn("> 公众号: Ada", md)
        # No `> 发布时间:` line because publish_time is missing.
        self.assertNotIn("发布时间", md)
        # No `> 原文链接:` line because source_url is missing.
        self.assertNotIn("原文链接", md)


if __name__ == "__main__":
    unittest.main()
