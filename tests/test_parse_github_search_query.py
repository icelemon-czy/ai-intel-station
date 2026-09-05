"""Regression tests for ``_parse_github`` search query type guard.

The previous code did ``str(item.get("query", "")).strip()`` which
returned the literal string "None" when the YAML had ``query: ~``
or ``query: null``. That silent coercion meant a search would run
with the broken query "None" instead of producing a validation
error the operator could act on.
"""
from __future__ import annotations

import unittest

from research.discovery.config_validation import _ErrorBag, _parse_github


class ParseGithubSearchQueryTests(unittest.TestCase):
    def test_string_query_passes(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github({"search": [{"query": "agent"}]}, errors)
        self.assertEqual(gh.search[0].query, "agent")
        self.assertEqual(len(errors.errors), 0)

    def test_null_query_records_an_error(self) -> None:
        # `query: ~` in YAML deserialises to None. The previous
        # behaviour coerced None to "None" via str(None) and ran a
        # broken search. The fix records an error.
        errors = _ErrorBag()
        gh = _parse_github({"search": [{"query": None}]}, errors)
        # The search entry is dropped — the operator sees the error
        # and the field is empty.
        self.assertEqual(gh.search, [])
        query_errors = [e for e in errors.errors if "query" in e.path]
        self.assertEqual(len(query_errors), 1)

    def test_missing_query_records_an_error(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github({"search": [{}]}, errors)
        self.assertEqual(gh.search, [])
        query_errors = [e for e in errors.errors if "query" in e.path]
        self.assertEqual(len(query_errors), 1)

    def test_whitespace_only_query_records_an_error(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github({"search": [{"query": "   "}]}, errors)
        # Whitespace alone is not a valid query — the existing
        # `if not query` check catches it.
        self.assertEqual(gh.search, [])
        query_errors = [e for e in errors.errors if "query" in e.path]
        self.assertEqual(len(query_errors), 1)


if __name__ == "__main__":
    unittest.main()
