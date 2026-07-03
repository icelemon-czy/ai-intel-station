"""Regression tests for ``collect.wechat.format_timestamp`` and
``extract_publish_time`` — previously these crashed on out-of-range
timestamps. A pathological WeChat page can produce such values via
JsDecode; before the fix, fetch_article died with an unhandled
ValueError instead of producing a usable markdown archive.
"""
from __future__ import annotations

import unittest

from collect.wechat import extract_publish_time, format_timestamp


class FormatTimestampTests(unittest.TestCase):
    def test_normal_timestamp(self) -> None:
        # Round-trip 1700000000 — the exact string just needs to be
        # parseable and stable; we don't want to lock in the wall-clock
        # value because the timezone handling is the contract being
        # pinned (UTC+8), not a specific day.
        result = format_timestamp(1700000000)
        # Must be a 19-char string like "YYYY-MM-DD HH:MM:SS".
        self.assertEqual(len(result), 19)
        self.assertEqual(result[4], "-")
        self.assertEqual(result[7], "-")
        self.assertEqual(result[10], " ")
        self.assertEqual(result[13], ":")
        self.assertEqual(result[16], ":")

    def test_zero_returns_repr_not_crash(self) -> None:
        # datetime.fromtimestamp(0) is valid but represents 1970-01-01 —
        # it's not actually a valid publish date, so the caller treats
        # this as 'unknown'. The buggy version used to raise — pinned
        # to the safe path.
        result = format_timestamp(0)
        self.assertEqual(result, "0")  # falls through to repr path

    def test_negative_timestamp_falls_back_to_repr(self) -> None:
        # A negative timestamp used to coerce via the timezone
        # offset into a 1970-01-01 07:59:59 string — silently
        # misrepresenting the post as a 1970 entry. The fix treats
        # any timestamp <= 0 as invalid.
        result = format_timestamp(-1234567890)
        self.assertEqual(result, "-1234567890")

    def test_far_future_timestamp_does_not_crash(self) -> None:
        # year 33658 is out of range → datetime raises OverflowError.
        # Without the fix this propagated out of fetch_article.
        result = format_timestamp(999999999999)
        self.assertIsInstance(result, str)
        # Falls back to repr() — opaque but non-empty so the user has a
        # signal that we couldn't format it.
        self.assertTrue(result)

    def test_negative_timestamp_does_not_crash(self) -> None:
        result = format_timestamp(-1234567890)
        self.assertIsInstance(result, str)


class ExtractPublishTimeTests(unittest.TestCase):
    def test_returns_empty_when_no_marker(self) -> None:
        self.assertEqual(extract_publish_time("<html>no markers</html>"), "")

    def test_jit_decode_form(self) -> None:
        # The most common shape pulled from a rendered WeChat page.
        html = "create_time : JsDecode('1700000000')"
        self.assertEqual(extract_publish_time(html), "2023-11-15 06:13:20")

    def test_quoted_digit_form(self) -> None:
        html = "create_time: '1700000000'"
        self.assertEqual(extract_publish_time(html), "2023-11-15 06:13:20")

    def test_unquoted_digit_form(self) -> None:
        html = "create_time: 1700000000"
        self.assertEqual(extract_publish_time(html), "2023-11-15 06:13:20")

    def test_returns_raw_string_when_jit_decode_not_numeric(self) -> None:
        # WeChat encodes the timestamp via JsDecode; the decoded value is
        # typically an integer but a misbehaving page could return a
        # non-numeric. The function must not raise — it returns the raw
        # string so the archive keeps the date verbatim.
        html = "create_time : JsDecode('not-a-number')"
        self.assertEqual(extract_publish_time(html), "not-a-number")


if __name__ == "__main__":
    unittest.main()
