from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

import collect.github as github_collect
import collect.papers as papers_collect
import collect.wechat as wechat_collect
import briefing.reports as briefing_reports
import research.discovery.runner as runner_module
from library.items import ResearchItem
from research.discovery import (
    BriefingConfig,
    DiscoveryConfig,
    GitHubSearchQuery,
    GitHubSource,
    PapersSource,
    SourceConfig,
    WeChatSource,
    collect_github,
    collect_papers,
    collect_wechat,
    generate_briefing,
    run_discovery,
)
from research.discovery.runner import _recent_enough


def _build_config(
    output_root: Path,
    *,
    github: GitHubSource | None = None,
    papers: PapersSource | None = None,
    wechat: WeChatSource | None = None,
    log_dir: Path | None = None,
    briefing: BriefingConfig | None = None,
    **limits: Any,
) -> DiscoveryConfig:
    config = DiscoveryConfig(output_root=output_root)
    if log_dir is not None:
        config.log_dir = log_dir
    if briefing is not None:
        config.briefing = briefing
    if limits:
        for key, value in limits.items():
            setattr(config.limits, key, value)
    config.sources = SourceConfig(
        github=github or config.sources.github,
        papers=papers or config.sources.papers,
        wechat=wechat or config.sources.wechat,
    )
    return config


def _fail(*args: Any, **kwargs: Any) -> None:
    raise AssertionError(f"network function should not run: {args!r} {kwargs!r}")


class DiscoveryRunnerTests(unittest.TestCase):
    """Each test captures whatever module-level mocks it needs at entry and
    restores them on exit. We avoid a mixin because unittest's discovery order
    is implementation-defined and setUp's getattr runs after a previous test
    may have already replaced the function."""

    def setUp(self) -> None:
        self._restore: list[tuple[Any, str, Any]] = []

    def tearDown(self) -> None:
        for module, attr, original in reversed(self._restore):
            if original is _SENTINEL:
                if hasattr(module, attr):
                    delattr(module, attr)
                continue
            setattr(module, attr, original)

    def _patch(self, module: Any, attr: str, replacement: Any) -> None:
        original = getattr(module, attr, _SENTINEL)
        self._restore.append((module, attr, original))
        setattr(module, attr, replacement)


_SENTINEL = object()


def test_recent_enough_handles_missing(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        self.assertFalse(_recent_enough(Path(tmp) / "missing", 24))


def test_recent_enough_detects_fresh_file(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fresh = Path(tmp) / "fresh"
        fresh.write_text("hello", encoding="utf-8")
        self.assertTrue(_recent_enough(fresh, 24))


def test_collect_github_dry_run_does_not_touch_network(self) -> None:
    self._patch(github_collect, "save_repo", _fail)
    self._patch(github_collect, "run_gh", _fail)
    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            github=GitHubSource(
                enabled=True,
                repos=["anthropics/claude-code"],
                search=[GitHubSearchQuery(query="agent harness", limit=3)],
            ),
        )
        report = collect_github(config, dry_run=True)
    self.assertEqual(report.succeeded, 2)
    self.assertTrue(all("dry-run" in note for note in report.notes))


def test_collect_github_skips_recently_collected(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        github_root = Path(tmp) / "github"
        repo_dir = github_root / "anthropics-claude-code"
        repo_dir.mkdir(parents=True)
        (repo_dir / "README.md").write_text("stale", encoding="utf-8")

        called: list[str] = []

        def _save_repo(owner: str, repo: str, output_dir: Path) -> None:
            called.append(f"{owner}/{repo}")

        self._patch(github_collect, "save_repo", _save_repo)
        config = _build_config(
            Path(tmp),
            github=GitHubSource(enabled=True, repos=["anthropics/claude-code"]),
        )
        report = collect_github(config)
    self.assertEqual(report.skipped, 1)
    self.assertEqual(called, [])


def test_collect_github_search_writes_results(self) -> None:
    written: list[tuple[str, Path]] = []

    def _save_search_results(query: str, output_dir: Path, repos: list[dict]) -> Path:
        path = output_dir / f"{query.replace(' ', '-')}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"q={query}\n", encoding="utf-8")
        written.append((query, path))
        return path

    self._patch(github_collect, "run_gh", lambda cmd: json.dumps([{"name": "x"}]))
    self._patch(github_collect, "save_search_results", _save_search_results)

    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            github=GitHubSource(
                enabled=True,
                search=[GitHubSearchQuery(query="agent harness", limit=3)],
            ),
        )
        report = collect_github(config)
    self.assertEqual(report.succeeded, 1)
    expected_path = Path(tmp) / "github" / "agent-harness.md"
    self.assertEqual(written, [("agent harness", expected_path)])


def test_collect_papers_invokes_fetch_and_save(self) -> None:
    fetch_calls: list[tuple[list[str], int]] = []
    save_calls: list[tuple[list[dict], str, Path]] = []

    def _fetch(
        categories: list[str],
        max_results: int = 10,
        **_kwargs: Any,
    ) -> list[dict]:
        fetch_calls.append((list(categories), max_results))
        return [{"title": f"Paper for {categories[0]}", "categories": categories}]

    def _save(papers: list[dict], category: str, output_dir: Path) -> None:
        save_calls.append((list(papers), category, output_dir))

    self._patch(papers_collect, "fetch_papers_by_category", _fetch)
    self._patch(papers_collect, "save_papers", _save)

    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            papers=PapersSource(enabled=True, categories=["cs.AI", "cs.LG"], max_per_category=4),
        )
        report = collect_papers(config)
    self.assertEqual(report.succeeded, 2)
    self.assertEqual(fetch_calls, [(["cs.AI"], 4), (["cs.LG"], 4)])
    self.assertEqual([c for _, c, _ in save_calls], ["cs.AI", "cs.LG"])


def test_collect_papers_truncates_by_limit(self) -> None:
    self._patch(
        papers_collect,
        "fetch_papers_by_category",
        lambda cats, max_results, **_kwargs: [],
    )
    self._patch(papers_collect, "save_papers", lambda *args, **kwargs: None)

    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            papers=PapersSource(
                enabled=True,
                categories=["cs.AI", "cs.LG", "cs.CL"],
                max_per_category=2,
            ),
            max_paper_categories=2,
        )
        report = collect_papers(config)
    # When fetch returns no papers we do not bump 'succeeded'; we expect
    # the truncation note and 'no papers returned' per category.
    self.assertEqual(report.skipped, 1)
    self.assertTrue(any("no papers returned" in note for note in report.notes))
    self.assertTrue(any("truncated" in note for note in report.notes))


def test_collect_papers_reports_failure_and_continues_next_category(self) -> None:
    saved: list[str] = []

    def _fetch(
        categories: list[str],
        max_results: int = 10,
        **_kwargs: Any,
    ) -> list[dict]:
        category = categories[0]
        if category == "cs.AI":
            raise RuntimeError("arXiv unavailable")
        return [
            {
                "title": "Recovered paper",
                "categories": [category],
            }
        ]

    self._patch(papers_collect, "fetch_papers_by_category", _fetch)
    self._patch(
        papers_collect,
        "save_papers",
        lambda papers, category, output_dir: saved.append(category),
    )

    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            papers=PapersSource(
                enabled=True,
                categories=["cs.AI", "cs.LG"],
                max_per_category=2,
            ),
        )
        report = collect_papers(config)

    self.assertEqual(report.failed, 1)
    self.assertEqual(report.succeeded, 1)
    self.assertEqual(saved, ["cs.LG"])
    self.assertTrue(any("cs.AI failed" in note for note in report.notes))


def test_collect_wechat_disabled_skips(self) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(Path(tmp))
        report = collect_wechat(config)
    self.assertFalse(report.enabled)
    self.assertEqual(report.succeeded, 0)


def test_collect_wechat_dry_run_does_not_invoke_browser(self) -> None:
    self._patch(wechat_collect, "fetch_article", _fail)
    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(
            Path(tmp),
            wechat=WeChatSource(enabled=True, urls=["https://mp.weixin.qq.com/s?__biz=foo"]),
        )
        report = collect_wechat(config, dry_run=True)
    self.assertEqual(report.succeeded, 1)


def test_generate_briefing_writes_markdown(self) -> None:
    item = ResearchItem(
        source="github",
        item_type="repository",
        title="Repo A",
        canonical_url="https://github.com/a/a",
        published_at="2099-01-01",
    )
    self._patch(runner_module, "query_research_items", lambda *args, **kwargs: [item])

    saved: list[Path] = []

    def _capture_reading_list(output_root, *, title, items, requested_sources=None):
        from publish.obsidian import briefing_output_path, write_markdown

        path = briefing_output_path(output_root, "reading-lists", title)
        lines = [f"# Reading List: {title}", ""]
        for it in items:
            lines.append(f"- [ ] [{it.title}]({it.canonical_url or ''})")
            if it.summary:
                lines.append(f"  - {it.summary}")
        write_markdown(path, "\n".join(lines))
        saved.append(path)
        print(f"DEBUG: capture output_root={output_root} path={path} exists={path.exists()}")
        return path

    self._patch(briefing_reports, "write_reading_list_report", _capture_reading_list)
    self._patch(briefing_reports, "write_digest_report", _capture_reading_list)

    with tempfile.TemporaryDirectory() as tmp:
        config = _build_config(Path(tmp))
        artifact = generate_briefing(config)
        self.assertIsNotNone(artifact)
        self.assertTrue(saved, "briefing markdown was not written")
        self.assertTrue(saved[0].name.startswith("daily-"))
        # Assert inside the with-block; the tempdir is cleaned up on exit.
        self.assertTrue(saved[0].is_file(), f"expected briefing file at {saved[0]}")
        self.assertIn("Repo A", saved[0].read_text(encoding="utf-8"))


def test_run_discovery_dry_run_skips_briefing_and_collect(self) -> None:
    self._patch(github_collect, "save_repo", _fail)
    self._patch(github_collect, "run_gh", _fail)
    self._patch(papers_collect, "fetch_papers_by_category", _fail)
    self._patch(papers_collect, "save_papers", _fail)
    self._patch(wechat_collect, "fetch_article", _fail)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        log_dir = tmp_path / "logs"
        config = _build_config(
            tmp_path,
            github=GitHubSource(enabled=True, repos=["anthropics/claude-code"]),
            papers=PapersSource(enabled=True, categories=["cs.AI"]),
            wechat=WeChatSource(enabled=True, urls=["https://mp.weixin.qq.com/s?__biz=foo"]),
            log_dir=log_dir,
        )
        report = run_discovery(config, dry_run=True, log_dir=log_dir)
    self.assertTrue(report.dry_run)
    self.assertEqual(report.sources["github"].succeeded, 1)
    self.assertEqual(report.sources["papers"].succeeded, 1)
    self.assertEqual(report.sources["wechat"].succeeded, 1)
    self.assertIsNotNone(report.briefing)
    self.assertEqual(report.briefing.path, Path("(dry-run)"))


def test_run_discovery_no_briefing_skips_briefing_step(self) -> None:
    self._patch(github_collect, "save_repo", _fail)
    self._patch(github_collect, "run_gh", _fail)
    self._patch(papers_collect, "fetch_papers_by_category", _fail)
    self._patch(papers_collect, "save_papers", _fail)
    self._patch(wechat_collect, "fetch_article", _fail)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        log_dir = tmp_path / "logs"
        config = _build_config(
            tmp_path,
            github=GitHubSource(enabled=True, repos=["anthropics/claude-code"]),
            briefing=BriefingConfig(enabled=True),
            log_dir=log_dir,
        )
        report = run_discovery(config, dry_run=True, log_dir=log_dir, enable_briefing=False)
    self.assertIsNone(report.briefing)


def test_run_discovery_only_filter_drops_other_sources(self) -> None:
    self._patch(github_collect, "save_repo", _fail)
    self._patch(github_collect, "run_gh", _fail)
    papers_collect.fetch_papers_by_category = lambda cats, max_results, **_kwargs: [
        {"title": "p", "categories": cats, "summary": "", "authors": [], "published": "", "updated": "", "arxiv_id": "", "pdf_url": "", "abs_url": ""}
    ]
    papers_collect.save_papers = lambda *args, **kwargs: None

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        log_dir = tmp_path / "logs"
        config = _build_config(
            tmp_path,
            github=GitHubSource(enabled=True, repos=["anthropics/claude-code"]),
            papers=PapersSource(enabled=True, categories=["cs.AI"]),
            wechat=WeChatSource(enabled=True, urls=["https://mp.weixin.qq.com/s?__biz=foo"]),
            log_dir=log_dir,
        )
        report = run_discovery(config, only=["papers"], dry_run=True, log_dir=log_dir)
    self.assertNotIn("github", report.sources)
    self.assertNotIn("wechat", report.sources)
    self.assertIn("papers", report.sources)


def test_run_discovery_writes_log_file(self) -> None:
    self._patch(github_collect, "save_repo", _fail)
    self._patch(github_collect, "run_gh", _fail)
    self._patch(papers_collect, "fetch_papers_by_category", _fail)
    self._patch(papers_collect, "save_papers", _fail)
    self._patch(wechat_collect, "fetch_article", _fail)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        log_dir = tmp_path / "logs"
        config = _build_config(
            tmp_path,
            github=GitHubSource(enabled=True, repos=["anthropics/claude-code"]),
            log_dir=log_dir,
        )
        report = run_discovery(config, dry_run=True, log_dir=log_dir)
        # Assert inside the with-block; the tempdir is cleaned up on exit.
        self.assertIsNotNone(report.log_path)
        self.assertTrue(report.log_path.is_file())
        contents = report.log_path.read_text(encoding="utf-8")
        self.assertIn("Summary:", contents)
        self.assertIn("succeeded=1", contents)


# Bind the free functions as methods on the test class for unittest discovery.
for _name, _fn in list(globals().items()):
    if _name.startswith("test_") and callable(_fn):
        setattr(DiscoveryRunnerTests, _name, _fn)


if __name__ == "__main__":
    unittest.main()
