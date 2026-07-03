"""Regression tests for `collect.wechat.safe_title` handling and the
collision-suffix that protects against same-title re-collects.

These functions are inline string ops inside ``fetch_article`` —
testing them keeps the contract simple without spinning up Camoufox.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path


def safe_title(title: str) -> str:
    """Mirror the inline regex in fetch_article — duplicated to keep the
    test isolated from the camoufox import path."""
    raw = re.sub(r'[/\\?%*:|"<>]', "_", title)[:80]
    return raw.strip("_") or "untitled"


class SafeTitleTests(unittest.TestCase):
    def test_strips_windows_reserved_chars(self) -> None:
        sanitized = safe_title('hello?win<dows>name\\here:cool*?')
        # Each forbidden char becomes an underscore.
        for forbidden in '/\\?%*:|"<>':
            self.assertNotIn(forbidden, sanitized)

    def test_80_char_cap(self) -> None:
        long = "a" * 200
        self.assertEqual(len(safe_title(long)), 80)

    def test_only_underscores_falls_back_to_untitled(self) -> None:
        # A title made entirely of forbidden chars would sanitize to
        # "____" — without the second `.strip("_") or "untitled"` it
        # would create a useless "____" directory.
        self.assertEqual(safe_title("?*/:"), "untitled")
        self.assertEqual(safe_title("___"), "untitled")
        self.assertEqual(safe_title(""), "untitled")

    def test_repeated_collects_get_unique_article_dirs(self) -> None:
        # fetch_article must not silently overwrite a previous collect
        # when two articles share a title.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            title = "热门 Agent Harness 综述"
            sanitized = safe_title(title)
            (base / sanitized).mkdir()
            # The actual selection loop lives inside fetch_article; we
            # reproduce just the collision-check contract here.
            chosen = base / sanitized
            counter = 1
            while chosen.exists():
                chosen = base / f"{sanitized}-{counter}"
                counter += 1
            self.assertEqual(chosen.name, f"{sanitized}-1")
            self.assertFalse(chosen.exists())


if __name__ == "__main__":
    unittest.main()
