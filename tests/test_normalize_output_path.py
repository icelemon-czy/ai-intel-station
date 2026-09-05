"""Regression tests for ``_normalize_output_path`` non-string input.

A previous version of ``_normalize_output_path`` did
``str(path).strip()`` without checking the input type. A caller
that passed a numeric sentinel (e.g. ``123``) — a real bug in a
fork where ``__post_init__`` once took the dataclass default for
a missing field — produced a literal ``"123"`` filename that
slipped through ``is_relative_to`` and ended up in
``build_paper_item`` as the markdown_path.
"""
from __future__ import annotations

import unittest

from ai_intel_station.library.items import _normalize_output_path


class NormalizeOutputPathNonStringTests(unittest.TestCase):
    def test_none_returns_none(self) -> None:
        self.assertIsNone(_normalize_output_path(None))

    def test_int_returns_none(self) -> None:
        # The bug shape: an int 123 used to produce
        # str(123).strip() = "123" — a literal filename.
        self.assertIsNone(_normalize_output_path(123))

    def test_list_returns_none(self) -> None:
        self.assertIsNone(_normalize_output_path([]))

    def test_dict_returns_none(self) -> None:
        self.assertIsNone(_normalize_output_path({"key": "value"}))

    def test_string_unchanged(self) -> None:
        self.assertEqual(
            _normalize_output_path("output/github/x/README.md"),
            "output/github/x/README.md",
        )

    def test_path_object_unchanged(self) -> None:
        from pathlib import Path
        result = _normalize_output_path(Path("output/x/README.md"))
        self.assertEqual(result, "output/x/README.md")


if __name__ == "__main__":
    unittest.main()
