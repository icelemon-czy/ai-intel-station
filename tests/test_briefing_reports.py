from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from briefing.reports import (
    _format_item,
    _local_link,
    build_digest_markdown,
    build_reading_list_markdown,
)
from library.items import ResearchItem


def _make_item(**kwargs):
    defaults = dict(
        source="github",
        item_type="repository",
        title="Repo X",
        canonical_url="https://github.com/x/x",
        summary="A short summary.",
        authors=["Alice", "Bob"],
        published_at="2026-06-01",
    )
    defaults.update(kwargs)
    return ResearchItem(**defaults)


class BriefingReportTests(unittest.TestCase):
    def test_local_link_strips_output_prefix(self) -> None:
        item = _make_item(output_path="output/github/x-x/README.md")
        self.assertEqual(_local_link(item), "../../github/x-x/README.md")

    def test_local_link_handles_dot_prefix(self) -> None:
        item = _make_item(output_path="./output/papers/foo.md")
        self.assertEqual(_local_link(item), "../../papers/foo.md")

    def test_local_link_returns_none_when_missing(self) -> None:
        item = _make_item(output_path=None)
        self.assertIsNone(_local_link(item))

    def test_format_item_digest_uses_external_link_first(self) -> None:
        item = _make_item(output_path="output/github/x-x/README.md")
        lines = _format_item(item, checked=False)
        text = "\n".join(lines)
        self.assertIn("[Repo X](https://github.com/x/x)", text)
        self.assertIn("[open local](../../github/x-x/README.md)", text)

    def test_format_item_reading_list_has_checkbox(self) -> None:
        item = _make_item(output_path=None)
        lines = _format_item(item, checked=True)
        text = "\n".join(lines)
        self.assertIn("[ ]", text)
        # No local link because output_path is None.
        self.assertNotIn("open local", text)

    def test_format_item_truncates_long_author_list(self) -> None:
        item = _make_item(
            output_path=None,
            authors=["Alice", "Bob", "Carol", "Dave", "Eve"],
        )
        text = "\n".join(_format_item(item, checked=False))
        self.assertIn("+2 more", text)

    def test_digest_markdown_renders_local_links(self) -> None:
        item = _make_item(output_path="output/github/x-x/README.md")
        md = build_digest_markdown("daily", [item], requested_sources=["github"])
        self.assertIn("# Digest: daily", md)
        self.assertIn("[Repo X](https://github.com/x/x)", md)
        self.assertIn("[open local](../../github/x-x/README.md)", md)

    def test_reading_list_markdown_renders_checkbox(self) -> None:
        item = _make_item(output_path="output/github/x-x/README.md")
        md = build_reading_list_markdown("daily", [item])
        self.assertIn("# Reading List: daily", md)
        self.assertIn("- [ ]", md)
        self.assertIn("[open local]", md)

    def test_digest_round_trip_write_and_read(self) -> None:
        """Briefing write produces a file containing the local link line."""
        from briefing.reports import write_digest_report

        item = _make_item(output_path="output/github/x-x/README.md")
        with tempfile.TemporaryDirectory() as tmp:
            out = write_digest_report(Path(tmp), "daily", [item])
            content = out.read_text(encoding="utf-8")
        self.assertIn("[open local](../../github/x-x/README.md)", content)


if __name__ == "__main__":
    unittest.main()