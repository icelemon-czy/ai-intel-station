"""Regression tests for the post-init path normalization and
briefing sort-by-recency contract.
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from briefing.reports import _sort_items, build_digest_markdown
from library.items import ResearchItem, _normalize_output_path, write_research_item


class NormalizeOutputPathTests(unittest.TestCase):
    def test_none_returns_none(self) -> None:
        self.assertIsNone(_normalize_output_path(None))

    def test_empty_string_returns_none(self) -> None:
        # Empty string is a common "no path" sentinel returned by some
        # upstream APIs — collapsing it to None keeps the
        # ``__post_init__`` filter consistent.
        self.assertIsNone(_normalize_output_path(""))

    def test_whitespace_only_returns_none(self) -> None:
        self.assertIsNone(_normalize_output_path("   "))
        self.assertIsNone(_normalize_output_path("\t\n"))


class PostInitCollapsesEmptyPath(unittest.TestCase):
    def test_item_with_empty_string_output_path_has_none(self) -> None:
        item = ResearchItem(
            source="github",
            item_type="repo",
            title="t",
            canonical_url="https://x",
            summary=None,
            authors=[],
            published_at=None,
            updated_at=None,
            tags=[],
            output_path="   ",  # whitespace — a no-op path
        )
        self.assertIsNone(item.output_path)


class BriefingSortByRecencyTests(unittest.TestCase):
    def _item(self, title, published_at):
        return ResearchItem(
            source="github",
            item_type="repo",
            title=title,
            canonical_url="https://example.com/" + title,
            summary="",
            authors=[],
            published_at=published_at,
            updated_at=None,
            tags=[],
            output_path=f"output/{title}.md",
        )

    def test_newest_first_within_same_source(self) -> None:
        older = self._item("agent", "2025-01-01")
        newer = self._item("bibliography", "2026-05-01")
        sorted_items = _sort_items([older, newer])
        # Newer publication date wins — even though 'bibliography' sorts
        # first alphabetically, recency takes priority.
        self.assertEqual([item.title for item in sorted_items], ["bibliography", "agent"])

    def test_unparseable_date_falls_back_to_alphabetical(self) -> None:
        good = self._item("agent-harness", "2026-05-01")
        bad = self._item("agentzero", "not-a-date")
        sorted_items = _sort_items([good, bad])
        # The bad date sorts as 0 — both items sort by title-ascending
        # under that key. agent-harness < agentzero alphabetically.
        self.assertEqual([item.title for item in sorted_items], ["agent-harness", "agentzero"])

    def test_digest_uses_recency_sort(self) -> None:
        older = self._item("alpha", "2025-01-01")
        newer = self._item("omega", "2026-05-01")
        md = build_digest_markdown("Recency", [older, newer])
        # Render order: omega (newer) appears before alpha in the digest.
        omega_idx = md.index("omega")
        alpha_idx = md.index("alpha")
        self.assertLess(omega_idx, alpha_idx)


if __name__ == "__main__":
    unittest.main()
