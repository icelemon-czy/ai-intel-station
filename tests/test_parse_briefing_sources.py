"""Regression tests for ``_parse_briefing`` source-list type guard.

The previous code did ``str(source).strip()`` which coerced a bare
number or a boolean to its string form. The follow-up membership
check ``s not in ('github', 'papers', 'wechat')`` then reported a
"not a valid source" error, but the user-facing message included
the coerced string which made the diagnosis confusing.

The fix now reports the type name so a user can immediately see
that they wrote a bare int / bool / list instead of a string.
"""
from __future__ import annotations

import unittest

from research.discovery.config import _ErrorBag, _parse_briefing


class ParseBriefingSourcesTests(unittest.TestCase):
    def test_string_list_passes(self) -> None:
        errors = _ErrorBag()
        b = _parse_briefing({"sources": ["github", "papers"]}, errors)
        self.assertEqual(b.sources, ["github", "papers"])
        self.assertEqual(len(errors.errors), 0)

    def test_int_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        b = _parse_briefing({"sources": [42]}, errors)
        # The bad entry is dropped, but an explicitly supplied list never
        # expands into unrequested default sources. load_config rejects the
        # accumulated error before the runtime can execute.
        self.assertEqual(b.sources, [])
        self.assertEqual(len(errors.errors), 1)
        self.assertIn("non-string", errors.errors[0].message)
        self.assertIn("int", errors.errors[0].message)

    def test_bool_entry_produces_friendly_error(self) -> None:
        # YAML treats ``enabled: true`` as a bool; a stray
        # ``sources: [true]`` used to coerce to "True" and fail
        # the membership check with a confusing message.
        errors = _ErrorBag()
        b = _parse_briefing({"sources": [True]}, errors)
        self.assertEqual(b.sources, [])
        self.assertIn("non-string", errors.errors[0].message)
        self.assertIn("bool", errors.errors[0].message)

    def test_dict_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        b = _parse_briefing({"sources": [{"name": "github"}]}, errors)
        self.assertEqual(b.sources, [])
        self.assertIn("non-string", errors.errors[0].message)
        self.assertIn("dict", errors.errors[0].message)


class ParseBriefingKeywordTests(unittest.TestCase):
    def test_default_keyword_when_missing(self) -> None:
        b = _parse_briefing({}, _ErrorBag())
        self.assertEqual(b.keyword, "daily")

    def test_explicit_keyword_preserved(self) -> None:
        b = _parse_briefing({"keyword": "agent"}, _ErrorBag())
        self.assertEqual(b.keyword, "agent")

    def test_explicit_null_keyword_falls_back_to_daily(self) -> None:
        # A YAML `keyword: ~` (or `keyword: null`) used to coerce
        # through str(None) = "None" — breaking the search downstream.
        b = _parse_briefing({"keyword": None}, _ErrorBag())
        self.assertEqual(b.keyword, "daily")

    def test_empty_string_keyword_falls_back_to_daily(self) -> None:
        b = _parse_briefing({"keyword": "  "}, _ErrorBag())
        self.assertEqual(b.keyword, "daily")


if __name__ == "__main__":
    unittest.main()
