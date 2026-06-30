from __future__ import annotations

import unittest
from pathlib import Path

from research.discovery import (
    GitHubSource,
    PapersSource,
    SourceConfig,
    WeChatSource,
    load_config,
    render_example_config,
)


def _write_yaml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "discovery.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def _load_or_fail(tmp_path: Path, yaml_text: str):
    try:
        return load_config(_write_yaml(tmp_path, yaml_text))
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"unexpected load_config failure: {exc}") from exc


def _expect_load_error(tmp_path: Path, yaml_text: str, needle: str) -> None:
    from research.discovery import DiscoveryConfigError

    try:
        load_config(_write_yaml(tmp_path, yaml_text))
    except DiscoveryConfigError as exc:
        assert needle in str(exc), f"expected {needle!r} in {exc}"
        return
    raise AssertionError("expected DiscoveryConfigError but got none")


class DiscoveryConfigTests(unittest.TestCase):
    def test_load_minimal_config_uses_defaults(self) -> None:
        from research.discovery.config import REPO_ROOT

        with self._tempdir() as tmp:
            config = _load_or_fail(Path(tmp), "sources: {}\nbriefing: {}\nlimits: {}\n")
        self.assertEqual(config.output_root, REPO_ROOT / "output")
        self.assertTrue(config.sources.github.enabled)
        self.assertEqual(config.sources.github.repos, [])
        self.assertEqual(config.sources.papers.categories, [])
        self.assertFalse(config.sources.wechat.enabled)
        self.assertEqual(config.briefing.mode, "reading-list")
        self.assertEqual(config.briefing.since_days, 1)
        self.assertEqual(config.limits.max_github_search_calls, 5)

    def test_load_full_config(self) -> None:
        yaml = """
output_root: output
log_dir: .ai/discovery

sources:
  github:
    enabled: true
    repos:
      - anthropics/claude-code
      - openai/swarm
    search:
      - query: "agent harness"
        limit: 3

  papers:
    enabled: true
    categories: [cs.AI, cs.LG]
    max_per_category: 5

  wechat:
    enabled: true
    urls:
      - "https://mp.weixin.qq.com/s?__biz=foo&mid=1"

briefing:
  enabled: true
  mode: digest
  keyword: "morning"
  sources: [github, papers]
  since_days: 2

limits:
  max_github_search_calls: 4
  max_paper_categories: 2
  skip_if_already_collected_hours: 8
"""
        with self._tempdir() as tmp:
            config = _load_or_fail(Path(tmp), yaml)
        self.assertEqual(config.sources.github.enabled, True)
        self.assertEqual(
            config.sources.github.repos,
            ["anthropics/claude-code", "openai/swarm"],
        )
        self.assertEqual(len(config.sources.github.search), 1)
        self.assertEqual(config.sources.github.search[0].query, "agent harness")
        self.assertEqual(config.sources.github.search[0].limit, 3)
        self.assertEqual(
            config.sources.papers,
            PapersSource(enabled=True, categories=["cs.AI", "cs.LG"], max_per_category=5),
        )
        self.assertTrue(config.sources.wechat.enabled)
        self.assertEqual(
            config.sources.wechat.urls,
            ["https://mp.weixin.qq.com/s?__biz=foo&mid=1"],
        )
        self.assertEqual(config.briefing.mode, "digest")
        self.assertEqual(config.briefing.keyword, "morning")
        self.assertEqual(config.briefing.sources, ["github", "papers"])
        self.assertEqual(config.briefing.since_days, 2)
        self.assertEqual(config.limits.max_github_search_calls, 4)
        self.assertEqual(config.limits.max_paper_categories, 2)
        self.assertEqual(config.limits.skip_if_already_collected_hours, 8)

    def test_load_rejects_unknown_paper_category(self) -> None:
        yaml = """
sources:
  papers:
    enabled: true
    categories: [cs.AI, cs.NOPE]
"""
        with self._tempdir() as tmp:
            _expect_load_error(Path(tmp), yaml, "unsupported values: cs.NOPE")

    def test_load_rejects_invalid_wechat_url(self) -> None:
        yaml = """
sources:
  wechat:
    enabled: true
    urls:
      - "https://example.com/foo"
"""
        with self._tempdir() as tmp:
            _expect_load_error(Path(tmp), yaml, "not a valid mp.weixin.qq.com URL")

    def test_load_rejects_invalid_briefing_mode(self) -> None:
        yaml = """
briefing:
  mode: monthly
"""
        with self._tempdir() as tmp:
            _expect_load_error(Path(tmp), yaml, "must be 'digest' or 'reading-list'")

    def test_load_rejects_missing_search_query(self) -> None:
        yaml = """
sources:
  github:
    search:
      - limit: 5
"""
        with self._tempdir() as tmp:
            _expect_load_error(Path(tmp), yaml, ".query")

    def test_load_missing_file_raises(self) -> None:
        from research.discovery import DiscoveryConfigError

        with self._tempdir() as tmp:
            with self.assertRaises(DiscoveryConfigError) as ctx:
                load_config(Path(tmp) / "missing.yaml")
        self.assertIn("Config file not found", str(ctx.exception))

    def test_load_aggregates_multiple_errors(self) -> None:
        from research.discovery import DiscoveryConfigError

        yaml = """
sources:
  github:
    search:
      - limit: 5
      - query: "ok"
  papers:
    enabled: true
    categories: [cs.AI, cs.NOPE]
    max_per_category: 0
briefing:
  mode: monthly
  since_days: -3
limits:
  max_paper_categories: -1
"""
        with self._tempdir() as tmp:
            with self.assertRaises(DiscoveryConfigError) as ctx:
                load_config(_write_yaml(Path(tmp), yaml))
        message = str(ctx.exception)
        # All problems must surface in one go, not stop at the first.
        self.assertIn("validation problem(s)", message)
        self.assertIn("search[0].query", message)
        self.assertIn("categories", message)
        self.assertIn("max_per_category", message)
        self.assertIn("briefing.mode", message)
        self.assertIn("briefing.since_days", message)
        self.assertIn("max_paper_categories", message)
        # And the message should NOT have stopped at the first failure.
        self.assertGreaterEqual(message.count("•"), 5)

    def test_load_reports_line_numbers(self) -> None:
        from research.discovery import DiscoveryConfigError

        yaml = (
            "sources:\n"
            "  github:\n"
            "    search:\n"
            "      - limit: 5\n"  # missing query on line 4
        )
        with self._tempdir() as tmp:
            with self.assertRaises(DiscoveryConfigError) as ctx:
                load_config(_write_yaml(Path(tmp), yaml))
        message = str(ctx.exception)
        self.assertIn("line 4", message)

    def test_render_example_config_is_valid_yaml(self) -> None:
        text = render_example_config()
        with self._tempdir() as tmp:
            config = _load_or_fail(Path(tmp), text)
        self.assertIsInstance(config.sources, SourceConfig)
        self.assertEqual(config.sources.wechat, WeChatSource(enabled=False, urls=[]))

    def _tempdir(self) -> "tempfile.TemporaryDirectory[str]":
        import tempfile

        return tempfile.TemporaryDirectory()


if __name__ == "__main__":
    unittest.main()