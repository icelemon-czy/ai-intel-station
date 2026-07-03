"""Regression tests for briefing link-text escaping and
DiscoveryLogger close behaviour.

``_format_item`` previously inlined ResearchItem.title and
canonical_url into a markdown link without escaping ']' — a title like
``"Python] beyond"`` produced a broken link that Obsidian rendered as
just "[Python". ``_escape_link_text`` now turns each ']' into ``\\]``
so the link survives.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from briefing.reports import _escape_link_text, _format_item, build_digest_markdown
from library.items import ResearchItem
from research.discovery.log import DiscoveryLogger


class EscapeLinkTextTests(unittest.TestCase):
    def test_escapes_closing_bracket(self) -> None:
        # The bug: a title with ']' broke [text](url) parsing.
        self.assertEqual(_escape_link_text("Python] beyond"), "Python\\] beyond")

    def test_leaves_text_alone_when_no_bracket(self) -> None:
        self.assertEqual(_escape_link_text("normal title"), "normal title")


class FormatItemLinkRoundtripTests(unittest.TestCase):
    def _item(self, title: str = "title", url: str = "https://x/y") -> ResearchItem:
        return ResearchItem(
            source="github",
            item_type="repo",
            title=title,
            canonical_url=url,
            summary="",
            authors=[],
            published_at="2026-05-01",
            tags=[],
            output_path="output/x/README.md",
        )

    def test_title_with_bracket_produces_well_formed_link(self) -> None:
        item = self._item(title="Python] beyond", url="https://example.com/x")
        lines = _format_item(item, checked=False)
        joined = "\n".join(lines)
        # The closing `]` in the title is now escaped, so the markdown
        # link round-trips correctly when Obsidian parses it.
        self.assertIn("[Python\\] beyond](https://example.com/x)", joined)

    def test_summary_with_newlines_keeps_indentation(self) -> None:
        item = self._item()
        item.summary = "first paragraph\nsecond paragraph"
        lines = _format_item(item, checked=False)
        # The second paragraph is indented by 4 spaces, not bare — it
        # stays inside the list item.
        joined = "\n".join(lines)
        self.assertIn("first paragraph\n    second paragraph", joined)


class BuildDigestMarkdownLinkContractTests(unittest.TestCase):
    def test_escaped_title_in_digest(self) -> None:
        item = ResearchItem(
            source="github",
            item_type="repo",
            title="Container]kit",
            canonical_url="https://example.com/containerkit",
            summary="a small CLI",
            authors=[],
            published_at="2026-05-01",
            tags=[],
            output_path="output/x/README.md",
        )
        md = build_digest_markdown("Werk", [item])
        self.assertIn("[Container\\]kit](https://example.com/containerkit)", md)


class DiscoveryLoggerCloseTests(unittest.TestCase):
    def test_close_writes_finished_marker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with DiscoveryLogger(log_dir) as logger:
                logger.log("hello world")
            content = Path(logger.path).read_text(encoding="utf-8")
            self.assertIn("hello world", content)
            self.assertIn("=== finished in", content)

    def test_log_after_close_does_not_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_dir = Path(tmp) / "logs"
            with DiscoveryLogger(log_dir) as logger:
                pass
            # log() called after close() — must not raise.  Falls back to
            # printing so the message still surfaces in the terminal.
            try:
                logger.log("trailing message")
            except Exception as exc:
                self.fail(f"log() after close raised {exc!r}")


if __name__ == "__main__":
    unittest.main()
