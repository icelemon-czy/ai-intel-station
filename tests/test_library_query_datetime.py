"""Edge-case unit tests for `library.query._parse_datetime` / `_matches_time_window`.

The previous version silently returned None for unparseable input,
which meant the Library form accepted `since=garbage` and returned
the entire archive. These tests pin down the new contract:
empty input → None; invalid input → ValueError.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from library.items import ResearchItem, write_research_item
from library.query import _parse_datetime, _matches_time_window
from workspace_web.service import list_library_items


class ParseDatetimeTests(unittest.TestCase):
    def test_empty_string_returns_none(self) -> None:
        self.assertIsNone(_parse_datetime(""))

    def test_none_returns_none(self) -> None:
        self.assertIsNone(_parse_datetime(None))

    def test_iso_date_parses(self) -> None:
        result = _parse_datetime("2026-05-08")
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 5)
        self.assertEqual(result.day, 8)

    def test_iso_datetime_with_z_parses(self) -> None:
        result = _parse_datetime("2026-05-08T00:00:00Z")
        self.assertEqual(result.year, 2026)

    def test_legacy_minute_precision_datetime_parses(self) -> None:
        result = _parse_datetime("2026-04-02 08:31")
        self.assertEqual(
            (result.year, result.month, result.day, result.hour, result.minute),
            (2026, 4, 2, 8, 31),
        )

    def test_garbage_raises_value_error(self) -> None:
        # The whole point of this contract: caller surfaces a 4xx so the
        # user is told their date filter is malformed, not silently
        # returned the unfiltered archive.
        with self.assertRaises(ValueError) as ctx:
            _parse_datetime("garbage-date")
        self.assertIn("garbage-date", str(ctx.exception))

    def test_partially_valid_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            _parse_datetime("2026/05/08")  # wrong separator


class MatchesTimeWindowTests(unittest.TestCase):
    """Verify item-side dates never raise even when malformed."""

    def _item(self, **overrides) -> MagicMock:
        item = MagicMock()
        item.published_at = overrides.get("published_at", "2026-05-01")
        item.updated_at = overrides.get("updated_at", None)
        return item

    def test_invalid_user_since_raises(self) -> None:
        item = self._item()
        with self.assertRaises(ValueError):
            _matches_time_window(item, since="bad-date", until=None)

    def test_invalid_item_date_does_not_raise(self) -> None:
        # Item-side dates come from real fetch — a malformed value
        # would crash the whole search if we propagated. The current
        # contract: with no since/until filter, even a malformed item
        # date yields a True match (no constraint to evaluate against
        # the bad data). The next test covers the "filter IS present"
        # case, where the bad item date drops the item silently.
        item = self._item(published_at="garbage")
        self.assertTrue(_matches_time_window(item, since=None, until=None))

    def test_invalid_item_date_dropped_when_filter_present(self) -> None:
        item = self._item(published_at="garbage")
        self.assertFalse(_matches_time_window(item, since="2026-01-01", until=None))

    def test_invalid_published_date_falls_back_to_valid_updated_date(self) -> None:
        item = self._item(
            published_at="garbage",
            updated_at="2026-05-02",
        )
        self.assertTrue(
            _matches_time_window(item, since="2026-05-01", until=None)
        )

    def test_no_window_matches(self) -> None:
        item = self._item(published_at="2026-05-01")
        self.assertTrue(_matches_time_window(item, since=None, until=None))


class LibraryQueryLegacyDatetimeRegressionTests(unittest.TestCase):
    def _write_item(
        self,
        output_root: Path,
        *,
        slug: str,
        title: str,
        published_at: str,
    ) -> None:
        item_dir = output_root / "github" / slug
        item_dir.mkdir(parents=True)
        markdown_path = item_dir / "README.md"
        markdown_path.write_text(f"# {title}\n", encoding="utf-8")
        write_research_item(
            ResearchItem(
                source="github",
                item_type="repository",
                title=title,
                published_at=published_at,
                output_path=str(markdown_path),
            ),
            item_dir / "research-item.json",
        )

    def test_public_library_query_accepts_legacy_minute_precision_datetime(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            self._write_item(
                output_root,
                slug="legacy",
                title="Legacy",
                published_at="2026-04-02 08:31",
            )
            self._write_item(
                output_root,
                slug="iso",
                title="ISO",
                published_at="2026-04-03T00:00:00Z",
            )

            payload = list_library_items(output_root)

        self.assertEqual(payload["total_count"], 2)
        self.assertEqual(
            [item["title"] for item in payload["items"]],
            ["ISO", "Legacy"],
        )

    def test_malformed_item_datetime_does_not_break_unfiltered_query(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            self._write_item(
                output_root,
                slug="valid",
                title="Valid",
                published_at="2026-04-03",
            )
            self._write_item(
                output_root,
                slug="malformed",
                title="Malformed",
                published_at="not-a-date",
            )

            unfiltered = list_library_items(output_root)
            filtered = list_library_items(output_root, since="2026-01-01")

        self.assertEqual(
            [item["title"] for item in unfiltered["items"]],
            ["Valid", "Malformed"],
        )
        self.assertEqual(
            [item["title"] for item in filtered["items"]],
            ["Valid"],
        )


if __name__ == "__main__":
    unittest.main()
