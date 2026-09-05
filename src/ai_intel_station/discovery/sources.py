from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import ai_intel_station.collect.github as github_module
import ai_intel_station.collect.hackernews as hackernews_module
import ai_intel_station.collect.papers as papers_module
import ai_intel_station.collect.wechat as wechat_module
import ai_intel_station.collect.wechat_index as wechat_index_module
import ai_intel_station.collect.x as x_module
from ai_intel_station.collect.papers import AI_CATEGORIES
from ai_intel_station.library.archive_paths import github_repo_leaf

from .config import DiscoveryConfig
from .log import DiscoveryLogger
from .models import SourceReport


def _recent_enough(path: Path, threshold_hours: int) -> bool:
    if not path.exists():
        return False
    age = datetime.now() - datetime.fromtimestamp(path.stat().st_mtime)
    return age.total_seconds() < threshold_hours * 3600


def _github_search_repos(query: str, limit: int, logger: DiscoveryLogger | None) -> list[dict]:
    payload = github_module.run_gh(
        [
            "search",
            "repos",
            query,
            "--sort",
            "updated",
            "--limit",
            str(limit),
            "--json",
            "name,owner,description,url,stargazersCount,createdAt,updatedAt",
        ]
    )
    return json.loads(payload)


def collect_github(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    github = config.sources.github
    report = SourceReport(name="github", enabled=github.enabled)

    if not github.enabled:
        report.notes.append("disabled in config")
        return report

    github_root = config.output_root / "github"
    search_calls = min(len(github.search), config.limits.max_github_search_calls)

    if dry_run:
        for repo in github.repos:
            report.notes.append(f"[dry-run] would refresh repo {repo}")
            report.succeeded += 1
        for query in github.search[:search_calls]:
            report.notes.append(f"[dry-run] would search '{query.query}' (limit={query.limit})")
            report.succeeded += 1
        if len(github.search) > search_calls:
            report.notes.append(
                f"[dry-run] skipped {len(github.search) - search_calls} search calls (limits.max_github_search_calls={search_calls})"
            )
            report.skipped += len(github.search) - search_calls
        return report

    github_root.mkdir(parents=True, exist_ok=True)
    skip_threshold = config.limits.skip_if_already_collected_hours

    for target in github.repos:
        if "/" not in target:
            report.notes.append(f"skip invalid repo target {target!r}")
            report.failed += 1
            continue
        owner, repo = target.split("/", 1)
        existing = github_root / github_repo_leaf(owner, repo)
        if _recent_enough(existing, skip_threshold):
            report.notes.append(f"skip {owner}/{repo} (collected within last {skip_threshold}h)")
            report.skipped += 1
            continue
        try:
            if logger:
                logger.log(f"📦 Fetching GitHub repo {owner}/{repo}...")
            result_path = github_module.save_repo(owner, repo, github_root)
            report.output_paths.append(result_path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{owner}/{repo} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {owner}/{repo}: {exc}")

    for query in github.search[:search_calls]:
        if logger:
            logger.log(f"🔍 GitHub search: '{query.query}' (limit={query.limit})")
        try:
            repos = _github_search_repos(query.query, query.limit, logger)
            result_path = github_module.save_search_results(query.query, github_root, repos)
            report.output_paths.append(result_path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"search '{query.query}' failed: {exc}")
            if logger:
                logger.log(f"  ❌ search '{query.query}': {exc}")

    if len(github.search) > search_calls:
        skipped = len(github.search) - search_calls
        report.skipped += skipped
        report.notes.append(
            f"skipped {skipped} search calls (limits.max_github_search_calls={search_calls})"
        )

    return report


def collect_hackernews(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    source = config.sources.hackernews
    report = SourceReport(name="hackernews", enabled=source.enabled)
    if not source.enabled:
        report.notes.append("disabled in config")
        return report
    if not source.feeds:
        report.failed = 1
        report.notes.append("no Hacker News feeds configured; realtime coverage is incomplete")
        return report
    if dry_run:
        for feed in source.feeds:
            report.succeeded += 1
            report.notes.append(
                f"[dry-run] would scan Hacker News {feed} (limit={source.limit}, keywords={source.keywords})"
            )
        return report

    output_root = config.output_root / "hackernews"
    for feed in source.feeds:
        try:
            if logger:
                logger.log(f"📰 Fetching Hacker News {feed}...")
            path = hackernews_module.collect_feed(
                feed,
                keywords=source.keywords,
                limit=source.limit,
                output_dir=output_root,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{feed} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {feed}: {exc}")
    return report


def collect_x(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    source = config.sources.x
    report = SourceReport(name="x", enabled=source.enabled)
    if not source.enabled:
        report.notes.append("disabled in config")
        return report
    if not source.queries:
        report.failed = 1
        report.notes.append("no X queries configured; realtime coverage is incomplete")
        return report
    if dry_run:
        for query in source.queries:
            report.succeeded += 1
            report.notes.append(
                f"[dry-run] would run X recent search {query!r} "
                f"(limit={source.limit}, freshness={config.briefing.freshness_hours}h, "
                f"token_env={source.token_env})"
            )
        return report

    output_root = config.output_root / "x"
    for query in source.queries:
        try:
            if logger:
                logger.log(f"𝕏 Recent search: {query!r}")
            path = x_module.collect_recent_search(
                query,
                token_env=source.token_env,
                limit=source.limit,
                output_dir=output_root,
                freshness_hours=config.briefing.freshness_hours,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{query!r} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {query!r}: {exc}")
    return report


def collect_papers(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    papers = config.sources.papers
    report = SourceReport(name="papers", enabled=papers.enabled)

    if not papers.enabled:
        report.notes.append("disabled in config")
        return report

    if not papers.categories:
        report.notes.append("no categories configured")
        return report

    categories = list(papers.categories)
    if len(categories) > config.limits.max_paper_categories:
        skipped = len(categories) - config.limits.max_paper_categories
        report.skipped += skipped
        report.notes.append(
            f"truncated {skipped} categories (limits.max_paper_categories={config.limits.max_paper_categories})"
        )
        categories = categories[: config.limits.max_paper_categories]

    if dry_run:
        for category in categories:
            report.notes.append(
                f"[dry-run] would fetch up to {papers.max_per_category} papers for {category} ({AI_CATEGORIES.get(category, '?')})"
            )
            report.succeeded += 1
        return report

    papers_root = config.output_root / "papers"
    papers_root.mkdir(parents=True, exist_ok=True)

    for category in categories:
        if logger:
            logger.log(f"📚 Fetching arXiv {category} ({AI_CATEGORIES.get(category, '?')})...")
        try:
            fetched = papers_module.fetch_papers_by_category(
                [category],
                papers.max_per_category,
                raise_on_error=True,
            )
            if not fetched:
                report.notes.append(f"{category}: no papers returned")
                continue
            papers_module.save_papers(fetched, category, papers_root)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{category} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {category}: {exc}")

    return report


def collect_wechat(
    config: DiscoveryConfig,
    logger: DiscoveryLogger | None = None,
    *,
    dry_run: bool = False,
) -> SourceReport:
    wechat = config.sources.wechat
    report = SourceReport(name="wechat", enabled=wechat.enabled)

    if not wechat.enabled:
        report.notes.append("disabled in config (default)")
        return report

    if not wechat.urls and not wechat.accounts:
        report.failed = 1
        report.notes.append("no WeChat URLs or accounts configured; realtime coverage is incomplete")
        return report

    if dry_run:
        for url in wechat.urls:
            report.notes.append(f"[dry-run] would fetch WeChat article {url}")
            report.succeeded += 1
        for account in wechat.accounts:
            report.notes.append(
                f"[dry-run] would query public WeChat index for {account.name} ({account.wechat_id})"
            )
            report.succeeded += 1
        return report

    wechat_root = config.output_root / "wechat"
    wechat_root.mkdir(parents=True, exist_ok=True)
    skip_threshold = config.limits.skip_if_already_collected_hours

    for url in wechat.urls:
        target = wechat_root / url.rsplit("/", 1)[-1].split("?")[0]
        # dedup by raw URL substring presence in any sidecar
        if any(url in str(path.read_text(errors="ignore")) for path in wechat_root.rglob("research-item.json") if path.exists()):
            if _recent_enough(target, skip_threshold) or any(_recent_enough(path, skip_threshold) for path in wechat_root.iterdir() if path.is_dir()):
                report.notes.append(f"skip {url} (recently collected)")
                report.skipped += 1
                continue
        try:
            if logger:
                logger.log(f"🦊 Fetching WeChat article: {url}")
            path = asyncio.run(wechat_module.fetch_article(url, output_dir=wechat_root))
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{url} failed: {exc}")
            if logger:
                logger.log(f"  ❌ {url}: {exc}")

    for account in wechat.accounts:
        try:
            if logger:
                logger.log(
                    f"🔎 WeChat public index: {account.name} ({account.wechat_id})"
                )
            path = wechat_index_module.collect_account(
                account.name,
                account.wechat_id,
                limit=wechat.index_limit,
                output_dir=wechat_root,
            )
            report.output_paths.append(path)
            report.succeeded += 1
        except Exception as exc:
            report.failed += 1
            report.notes.append(f"{account.name} index failed: {exc}")
            if logger:
                logger.log(f"  ❌ {account.name}: {exc}")

    return report
