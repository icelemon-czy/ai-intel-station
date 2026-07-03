"""Regression tests for ``_parse_github`` repo-list type guard.

The previous code did ``str(item).strip()`` which produced a noisy
``"{'name': 'x/y'}"`` for a mapping value and let the bad entry
through to the GitHub CLI as if it were a valid owner/repo. Now
non-string entries produce a friendly error in the aggregated
``DiscoveryConfigError`` instead of polluting the gh invocation.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.discovery.config import (
    DiscoveryConfig,
    DiscoveryConfigError,
    _ErrorBag,
    _parse_github,
)


def _write_yaml(body: str) -> Path:
    tmp = Path(tempfile.mkstemp(suffix=".yaml")[1])
    tmp.write_text(body, encoding="utf-8")
    return tmp


class ParseGithubReposTests(unittest.TestCase):
    def test_string_list_passes(self) -> None:
        gh = _parse_github({"repos": ["x/y", "a/b"]}, _ErrorBag())
        self.assertEqual(gh.repos, ["x/y", "a/b"])
        self.assertTrue(gh.enabled)

    def test_dict_entry_produces_friendly_error(self) -> None:
        # YAML typo: user wrote `repos: [{name: x/y}]` instead of
        # `repos: [x/y]`. The previous code coerced the dict to a
        # noisy string and pushed it into the gh CLI as a fake
        # owner/repo, which then failed with a confusing message.
        errors = _ErrorBag()
        gh = _parse_github({"repos": [{"name": "x/y"}]}, errors)
        self.assertEqual(gh.repos, [])
        self.assertEqual(len(errors.errors), 1)
        self.assertEqual(errors.errors[0].path, "sources.github.repos[0]")

    def test_int_entry_produces_friendly_error(self) -> None:
        errors = _ErrorBag()
        gh = _parse_github({"repos": [42]}, errors)
        self.assertEqual(gh.repos, [])
        self.assertEqual(len(errors.errors), 1)

    def test_empty_strings_dropped(self) -> None:
        # An empty / whitespace-only repo entry should be skipped
        # silently, not produce an error.
        errors = _ErrorBag()
        gh = _parse_github({"repos": ["", "  ", "x/y"]}, errors)
        self.assertEqual(gh.repos, ["x/y"])
        self.assertEqual(len(errors.errors), 0)

    def test_load_config_aggregates_repos_error(self) -> None:
        # End-to-end: a config with a dict entry under repos must
        # raise a single DiscoveryConfigError that mentions the
        # offending path.
        path = _write_yaml(
            "output_root: output\n"
            "log_dir: .ai/L4-session/discovery\n"
            "sources:\n"
            "  github:\n"
            "    enabled: true\n"
            "    repos:\n"
            "      - { name: x/y }\n"
            "limits: {}\n"
        )
        with self.assertRaises(DiscoveryConfigError) as ctx:
            from research.discovery.config import load_config
            load_config(path)
        # The aggregated error message mentions the bad path.
        self.assertIn("sources.github.repos[0]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
