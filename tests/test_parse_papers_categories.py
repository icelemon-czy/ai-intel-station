"""Regression tests for ``_parse_papers`` categories type guard.

The previous code coerced a non-string entry with ``str(item)`` —
a YAML typo like ``categories: [42]`` produced the literal string
"42", which then failed the AI_CATEGORIES membership check with a
confusing "unsupported values: 42" message. The new contract
rejects non-string entries with a friendly type-name error.
"""
from __future__ import annotations

import unittest

from research.discovery.config_validation import _ErrorBag, _parse_papers


class ParsePapersCategoriesTests(unittest.TestCase):
    def test_string_list_passes(self) -> None:
        errors = _ErrorBag()
        p = _parse_papers({"categories": ["cs.AI", "cs.LG"]}, errors)
        self.assertEqual(p.categories, ["cs.AI", "cs.LG"])
        self.assertEqual(len(errors.errors), 0)

    def test_int_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        p = _parse_papers({"categories": [42]}, errors)
        # The bad entry is dropped; the categories list reflects only
        # valid strings.
        self.assertEqual(p.categories, [])
        self.assertEqual(len(errors.errors), 1)
        self.assertIn("must be a string", errors.errors[0].message)
        self.assertIn("int", errors.errors[0].message)

    def test_bool_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        p = _parse_papers({"categories": [True]}, errors)
        self.assertEqual(p.categories, [])
        self.assertIn("must be a string", errors.errors[0].message)
        self.assertIn("bool", errors.errors[0].message)

    def test_dict_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        p = _parse_papers({"categories": [{"name": "cs.AI"}]}, errors)
        self.assertEqual(p.categories, [])
        self.assertIn("must be a string", errors.errors[0].message)
        self.assertIn("dict", errors.errors[0].message)

    def test_string_unknown_category_records_error(self) -> None:
        # A valid string but not in AI_CATEGORIES surfaces the
        # existing 'unsupported values' error so the operator can
        # see which category is wrong.
        errors = _ErrorBag()
        _parse_papers({"categories": ["cs.NOPE"]}, errors)
        unsupported = [e for e in errors.errors if "unsupported" in e.message]
        self.assertEqual(len(unsupported), 1)
        self.assertIn("cs.NOPE", unsupported[0].message)


if __name__ == "__main__":
    unittest.main()
