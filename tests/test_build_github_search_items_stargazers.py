"""Regression tests for ``build_github_search_items`` stargazer_count.

The previous code used ``or`` to fall back from
``stargazersCount`` to ``stargazerCount``. The ``or`` operator
treats ``0`` (a valid stargazer count) as falsy and fell through
to the alternate key, so a repo with zero stars reported ``None``
in the metadata instead of ``0``.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from library.items import build_github_search_items


class BuildGithubSearchItemsStargazersTests(unittest.TestCase):
    def test_zero_stars_preserved_as_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "search.md"
            items = build_github_search_items(
                "zero",
                [
                    {
                        "name": "empty",
                        "owner": {"login": "x"},
                        "url": "https://github.com/x/empty",
                        "stargazersCount": 0,
                        "description": "no stars",
                    }
                ],
                md,
            )
            self.assertEqual(items[0].metadata["stargazer_count"], 0)

    def test_nonzero_stars_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "search.md"
            items = build_github_search_items(
                "real",
                [
                    {
                        "name": "real",
                        "owner": {"login": "x"},
                        "url": "https://github.com/x/real",
                        "stargazersCount": 42,
                        "description": "forty two",
                    }
                ],
                md,
            )
            self.assertEqual(items[0].metadata["stargazer_count"], 42)


if __name__ == "__main__":
    unittest.main()
