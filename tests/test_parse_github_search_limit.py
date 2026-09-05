"""Regression tests for ``_parse_github`` search-block validation.

The previous code iterated ``for err in errors`` to check whether a
limit error was already recorded (so it wouldn't double-log). The
_ErrorBag class is not iterable — it stores errors on ``.errors``.
That meant a negative ``limit`` produced a follow-up TypeError
mid-validation when the search had multiple entries.
"""
from __future__ import annotations

import unittest

from ai_intel_station.discovery.config import DiscoveryConfigError
from ai_intel_station.discovery.config_validation import _ErrorBag, _parse_github


class ParseGithubSearchLimitTests(unittest.TestCase):
    def test_negative_limit_produces_single_error(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github(
            {"search": [{"query": "agent", "limit": -5}]},
            errors,
        )
        # The search entry is KEPT with the default limit of 10 so the
        # operator can see the query alongside the error message. Only
        # the limit value is replaced.
        self.assertEqual(len(gh.search), 1)
        self.assertEqual(gh.search[0].query, "agent")
        self.assertEqual(gh.search[0].limit, 10)
        # Exactly one error reported, not two.
        limit_errors = [e for e in errors.errors if e.path.endswith(".limit")]
        self.assertEqual(len(limit_errors), 1)
        self.assertIn("must be positive", limit_errors[0].message)

    def test_non_integer_limit_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github(
            {"search": [{"query": "agent", "limit": "many"}]},
            errors,
        )
        limit_errors = [e for e in errors.errors if e.path.endswith(".limit")]
        self.assertEqual(len(limit_errors), 1)
        # The non-integer default is 10 (preserves the entry).
        self.assertEqual(gh.search[0].limit, 10)
        self.assertEqual(gh.search[0].query, "agent")

    def test_iter_errors_does_not_raise(self) -> None:
        # The original bug: ``for err in errors`` raised
        # TypeError: 'ErrorBag' object is not iterable when the
        # search had a non-positive limit. Pin it down so a future
        # refactor cannot regress the iteration.
        errors = _ErrorBag()
        _parse_github(
            {"search": [{"query": "agent", "limit": -5}]},
            errors,
        )
        # The internal `any(err.path.endswith(".limit") for err in errors.errors)`
        # is the contract. We just verify that _ErrorBag is NOT
        # directly iterable (so the bug would surface loudly if the
        # pattern regresses) — i.e. iterating fails.
        with self.assertRaises(TypeError):
            for _ in errors:  # type: ignore[attr-defined]
                pass


if __name__ == "__main__":
    unittest.main()
