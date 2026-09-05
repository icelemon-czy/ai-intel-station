from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from library.items import ResearchItem, write_research_item


def _signal(
    title: str,
    *,
    source: str = "hackernews",
    url: str | None = None,
    published_at: str,
    watchlist: bool = False,
    engagement: int = 0,
    summary: str | None = None,
) -> ResearchItem:
    return ResearchItem(
        source=source,
        item_type="story",
        title=title,
        canonical_url=url or f"https://example.com/{title.lower().replace(' ', '-')}",
        summary=summary,
        published_at=published_at,
        discovered_at="2026-08-13T01:00:00Z",
        signal_role="signal",
        discovery_method="test-fixture",
        metadata={"watchlist": watchlist, "engagement_count": engagement},
    )


def _evidence(
    title: str,
    *,
    source: str = "github",
    url: str | None = None,
    published_at: str = "2026-08-13T00:00:00Z",
    updated_at: str | None = None,
) -> ResearchItem:
    return ResearchItem(
        source=source,
        item_type="repository" if source == "github" else "paper",
        title=title,
        canonical_url=url or f"https://example.com/{title.lower().replace(' ', '-')}",
        published_at=published_at,
        updated_at=updated_at,
        signal_role="evidence",
        discovery_method="test-fixture",
    )

def test_renderer_separates_hn_target_from_discussion_and_preserves_other_sources() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    hn = _signal(
        "GitHub launch",
        url="https://github.com/example/launch",
        published_at="2026-08-13T00:50:00Z",
    )
    hn.metadata["discussion_url"] = "https://news.ycombinator.com/item?id=123"
    x_signal = _signal(
        "X signal",
        source="x",
        url="https://x.com/example/status/1",
        published_at="2026-08-13T00:40:00Z",
    )
    wechat = _signal(
        "WeChat signal",
        source="wechat",
        url="https://mp.weixin.qq.com/s/example",
        published_at="2026-08-13T00:30:00Z",
    )
    selection = select_daily_briefing(
        [hn, x_signal, wechat],
        now=now,
        hackernews_items=1,
        wechat_max_items=2,
        x_items=1,
        github_items=0,
        paper_items=0,
    )
    reports = {
        source: SourceReport(name=source, enabled=True, succeeded=1)
        for source in ("hackernews", "x", "wechat")
    }
    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        viable_news_sources=list(reports),
    )

    assert "[GitHub launch](https://github.com/example/launch)" in rendered.markdown
    assert "[hackernews](https://news.ycombinator.com/item?id=123)" in rendered.markdown
    assert "[x](https://x.com/example/status/1)" in rendered.markdown
    assert "[wechat](https://mp.weixin.qq.com/s/example)" in rendered.markdown

    historical = _signal(
        "Historical HN",
        url="https://github.com/example/historical",
        published_at="2026-08-13T00:20:00Z",
    )
    historical_rendered = render_daily_signal_markdown(
        "historical",
        select_daily_briefing(
            [historical],
            now=now,
            hackernews_items=1,
            github_items=0,
            paper_items=0,
        ),
        {"hackernews": reports["hackernews"]},
        now=now,
        coverage_sources=["hackernews"],
        viable_news_sources=["hackernews"],
    )
    assert "[hackernews](https://github.com/example/historical)" in historical_rendered.markdown


def test_render_daily_signal_briefing_ready_partial_and_empty_statuses() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_signals
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    entries = select_daily_signals(
        [_signal("New thing", published_at="2026-08-13T00:30:00Z")],
        now=now,
        freshness_hours=48,
        max_items=5,
    )
    complete = {
        "hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1),
        "wechat": SourceReport(name="wechat", enabled=False),
    }
    failed = {
        **complete,
        "x": SourceReport(name="x", enabled=True, failed=1, notes=["token unavailable"]),
    }

    ready = render_daily_signal_markdown("daily", entries, complete, now=now)
    partial = render_daily_signal_markdown("daily", entries, failed, now=now)
    empty = render_daily_signal_markdown("daily", [], complete, now=now)
    incomplete = render_daily_signal_markdown("daily", [], failed, now=now)

    assert ready.status == "ready"
    assert "> Status: ready" in ready.markdown
    assert "是什么" in ready.markdown and "为什么现在值得看" in ready.markdown
    assert partial.status == "partial" and "token unavailable" in partial.markdown
    assert empty.status == "no_fresh_signals"
    assert "No verified fresh signals" in empty.markdown
    assert incomplete.status == "coverage_incomplete"
    assert "coverage is incomplete" in incomplete.markdown


def test_quota_renderer_groups_lanes_and_reports_honest_coverage() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [
            _signal(
                "Only HN",
                source="hackernews",
                published_at="2026-08-13T00:30:00Z",
            ),
            _evidence(
                "Repo",
                source="github",
                published_at="2026-08-12T22:00:00Z",
                updated_at="2026-08-13T00:40:00Z",
            ),
            _evidence(
                "Paper",
                source="papers",
                published_at="2026-08-13T00:20:00Z",
            ),
        ],
        now=now,
        hackernews_items=1,
        wechat_min_items=1,
        github_items=1,
        paper_items=1,
    )
    reports = {
        "hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1),
        "github": SourceReport(name="github", enabled=True, succeeded=1),
        "papers": SourceReport(name="papers", enabled=True, succeeded=1),
        "wechat": SourceReport(
            name="wechat", enabled=True, failed=1, notes=["public index unavailable"]
        ),
    }

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=["hackernews", "github", "papers", "wechat"],
        required_sources=["github", "papers", "wechat"],
        viable_news_sources=["hackernews", "wechat"],
    )

    assert rendered.status == "partial"
    assert "## arXiv" in rendered.markdown
    assert "## GitHub" in rendered.markdown
    assert "## Hacker News" in rendered.markdown
    assert "| WeChat minimum | 1 | 0 | 1 |" in rendered.markdown
    assert "public index unavailable" in rendered.markdown


def test_wechat_quota_shortfall_alone_makes_nonempty_result_partial() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("HN fills News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        hackernews_items=1,
        wechat_min_items=1,
        github_items=0,
        paper_items=0,
    )
    reports = {
        "hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1),
        "wechat": SourceReport(name="wechat", enabled=True, succeeded=1),
    }

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        required_sources=["wechat"],
        viable_news_sources=["hackernews", "wechat"],
    )

    assert rendered.status == "partial"
    assert "| WeChat minimum | 1 | 0 | 1 |" in rendered.markdown


def test_optional_wechat_failure_does_not_downgrade_completed_news_coverage() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    reports = {
        "hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1),
        "wechat": SourceReport(
            name="wechat", enabled=True, failed=1, notes=["public index unavailable"]
        ),
    }
    selection = select_daily_briefing(
        [_signal("HN fills News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        wechat_max_items=1,
        github_items=0,
        paper_items=0,
    )

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        viable_news_sources=["hackernews", "wechat"],
        optional_sources=["wechat"],
    )
    empty = render_daily_signal_markdown(
        "daily-empty",
        select_daily_briefing(
            [],
            now=now,
            hackernews_items=1,
            wechat_min_items=0,
            wechat_max_items=1,
            github_items=0,
            paper_items=0,
        ),
        reports,
        now=now,
        coverage_sources=list(reports),
        viable_news_sources=["hackernews", "wechat"],
        optional_sources=["wechat"],
    )

    assert rendered.status == "ready"
    assert empty.status == "no_fresh_signals"
    assert "optional-failed" in rendered.markdown
    assert "public index unavailable" in rendered.markdown
    assert "attempted source failed: wechat" not in rendered.markdown


def test_optional_wechat_failure_still_blocks_when_it_is_the_only_news_provider() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    reports = {
        "wechat": SourceReport(name="wechat", enabled=True, failed=1, notes=["blocked"])
    }
    options = {
        "now": now,
        "coverage_sources": ["wechat"],
        "viable_news_sources": ["wechat"],
        "optional_sources": ["wechat"],
    }
    nonempty_selection = select_daily_briefing(
        [_signal("Cached News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        wechat_max_items=1,
        github_items=0,
        paper_items=0,
    )
    empty_selection = select_daily_briefing(
        [],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        wechat_max_items=1,
        github_items=0,
        paper_items=0,
    )

    nonempty = render_daily_signal_markdown("daily", nonempty_selection, reports, **options)
    empty = render_daily_signal_markdown("daily", empty_selection, reports, **options)

    assert nonempty.status == "partial"
    assert empty.status == "coverage_incomplete"
    assert "attempted source failed: wechat" in nonempty.markdown


def test_optional_wechat_exception_does_not_hide_x_failure() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("HN fills News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        wechat_max_items=1,
        github_items=0,
        paper_items=0,
    )
    reports = {
        "hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1),
        "wechat": SourceReport(name="wechat", enabled=True, failed=1),
        "x": SourceReport(name="x", enabled=True, failed=1),
    }

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        viable_news_sources=["hackernews", "wechat", "x"],
        optional_sources=["wechat"],
    )

    assert rendered.status == "partial"
    assert "attempted source failed: x" in rendered.markdown
    assert "attempted source failed: wechat" not in rendered.markdown


def test_quota_renderer_marks_unattempted_news_and_required_lane_incomplete() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    local_news = _signal("Local sidecar", published_at="2026-08-13T00:30:00Z")
    selection = select_daily_briefing(
        [local_news],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        {
            "github": SourceReport(name="github", enabled=True, succeeded=1),
            "papers": SourceReport(name="papers", enabled=True, succeeded=1),
        },
        now=now,
        coverage_sources=["hackernews", "github", "papers"],
        required_sources=["github", "papers"],
        viable_news_sources=["hackernews"],
    )

    assert rendered.status == "partial"
    assert "Local sidecar" in rendered.markdown
    assert "unattempted News coverage" in rendered.markdown

    empty = select_daily_briefing(
        [],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )
    empty_rendered = render_daily_signal_markdown(
        "daily",
        empty,
        {},
        now=now,
        coverage_sources=["hackernews", "github", "papers"],
        required_sources=["github", "papers"],
        viable_news_sources=["hackernews"],
    )
    assert empty_rendered.status == "coverage_incomplete"


@pytest.mark.parametrize("failed_source", ["github", "papers", "wechat"])
def test_quota_renderer_counts_all_selected_source_failures(
    failed_source: str,
) -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("usable", published_at="2026-08-13T00:30:00Z")],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=0,
    )
    reports = {
        source: SourceReport(
            name=source,
            enabled=True,
            failed=1 if source == failed_source else 0,
        )
        for source in ("hackernews", "github", "papers", "wechat")
    }

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        viable_news_sources=["hackernews"],
    )

    assert rendered.status == "partial"
    assert f"attempted source failed: {failed_source}" in rendered.markdown


def test_quota_renderer_complete_empty_success_is_no_fresh_signals() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_briefing
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )
    reports = {
        source: SourceReport(name=source, enabled=True)
        for source in ("hackernews", "github", "papers")
    }

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        reports,
        now=now,
        coverage_sources=list(reports),
        required_sources=["github", "papers"],
        viable_news_sources=["hackernews"],
    )

    assert rendered.status == "no_fresh_signals"
    assert "| Hacker News | 1 | 0 | 1 |" in rendered.markdown


def test_signal_markdown_escapes_untrusted_titles_and_coverage_notes() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_signals
    from research.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    signal = _signal(
        "unsafe]\nheading",
        published_at="2026-08-13T00:30:00Z",
        summary="first line\n- injected bullet",
    )
    entries = select_daily_signals([signal], now=now)
    rendered = render_daily_signal_markdown(
        "daily",
        entries,
        {
            "hackernews": SourceReport(
                name="hackernews", enabled=True, failed=1, notes=["bad | row\nnext"]
            )
        },
        now=now,
    )

    assert "unsafe\\] heading" in rendered.markdown
    assert "first line - injected bullet" in rendered.markdown
    assert "bad \\| row next" in rendered.markdown


def test_signal_briefing_is_bounded_to_five_items() -> None:
    from briefing.signal_rendering import render_daily_signal_markdown
    from briefing.signals import select_daily_signals

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    entries = select_daily_signals(
        [
            _signal(
                f"signal {index}",
                published_at=(now - timedelta(minutes=index)).isoformat(),
            )
            for index in range(8)
        ],
        now=now,
        max_items=5,
    )
    rendered = render_daily_signal_markdown("daily", entries, {}, now=now)

    assert len(entries) == 5
    assert rendered.markdown.count("\n### ") == 5


def test_generate_signal_briefing_filters_to_configured_sources(
    tmp_path: Path,
) -> None:
    from research.discovery import BriefingConfig, DiscoveryConfig
    from research.discovery.runner import generate_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    hn = _signal("Allowed HN", published_at="2026-08-13T00:30:00Z")
    wechat = _signal(
        "Excluded WeChat",
        source="wechat",
        published_at="2026-08-13T00:30:00Z",
    )
    write_research_item(hn, tmp_path / "hackernews" / "hn" / "research-item.json")
    write_research_item(wechat, tmp_path / "wechat" / "wx" / "research-item.json")
    config = DiscoveryConfig(
        output_root=tmp_path,
        log_dir=tmp_path / "logs",
        briefing=BriefingConfig(
            mode="signals",
            sources=["hackernews"],
            freshness_hours=48,
            max_items=5,
        ),
    )

    artifact = generate_briefing(config, now=now, source_reports={})

    assert artifact is not None and artifact.path is not None
    markdown = artifact.path.read_text(encoding="utf-8")
    assert "Allowed HN" in markdown
    assert "Excluded WeChat" not in markdown


def test_quota_dry_run_reports_github_news_maximum_without_fake_actuals(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from research.discovery import BriefingConfig, DiscoveryConfig, DiscoveryLogger
    from research.discovery.runner import generate_briefing

    config = DiscoveryConfig(
        output_root=tmp_path,
        log_dir=tmp_path / "logs",
        briefing=BriefingConfig(
            mode="signals",
            hackernews_items=5,
            wechat_min_items=0,
            wechat_max_items=2,
            github_items=1,
            paper_items=1,
            quota_mode=True,
        ),
    )

    with DiscoveryLogger(config.log_dir) as logger:
        artifact = generate_briefing(config, report_log=logger, dry_run=True)

    output = capsys.readouterr().out
    assert artifact is not None and artifact.status == "dry_run"
    assert "5 Hacker News" in output
    assert "WeChat optional maximum=2" in output
    assert "1 GitHub" in output
    assert "1 arXiv" in output
    assert "GitHub destinations" not in output


def test_nondefault_github_news_maximum_flows_from_yaml_through_runner(
    tmp_path: Path,
) -> None:
    from research.discovery import SourceReport, load_config
    from research.discovery.runner import generate_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    for index, item in enumerate(
        [
            _signal(
                "Repo launch one",
                url="https://github.com/example/one",
                published_at="2026-08-13T00:50:00Z",
                engagement=30,
            ),
            _signal(
                "Repo launch two",
                url="https://gist.github.com/example/two",
                published_at="2026-08-13T00:40:00Z",
                engagement=20,
            ),
            _signal(
                "External analysis",
                url="https://news.example.com/analysis",
                published_at="2026-08-13T00:30:00Z",
                engagement=10,
            ),
        ]
    ):
        write_research_item(
            item,
            tmp_path / "hackernews" / str(index) / "research-item.json",
        )
    config_path = tmp_path / "discovery.yaml"
    config_path.write_text(
        f"""
output_root: {tmp_path.as_posix()}
log_dir: {(tmp_path / 'logs').as_posix()}
sources:
  github: {{enabled: false}}
  papers: {{enabled: false}}
  wechat: {{enabled: false}}
  hackernews: {{enabled: true, feeds: [newstories]}}
  x: {{enabled: false}}
briefing:
  mode: signals
  sources: [hackernews]
  news_items: 1
  wechat_max_items: 0
  github_news_max_items: 0
  github_items: 0
  paper_items: 0
limits: {{}}
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    artifact = generate_briefing(
        config,
        now=now,
        source_reports={
            "hackernews": SourceReport(
                name="hackernews",
                enabled=True,
                succeeded=1,
            )
        },
    )

    assert config.briefing.hackernews_items == 1
    assert artifact is not None and artifact.status == "ready"
    markdown = artifact.path.read_text(encoding="utf-8")
    assert "Repo launch one" in markdown
    assert "GitHub destinations" not in markdown


def test_generate_quota_briefing_runs_real_production_path_with_seven_items(
    tmp_path: Path,
) -> None:
    from research.discovery import (
        BriefingConfig,
        DiscoveryConfig,
        GitHubSource,
        HackerNewsSource,
        PapersSource,
        SourceConfig,
        WeChatAccount,
        WeChatSource,
    )
    from research.discovery.models import SourceReport
    from research.discovery.runner import generate_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    items = [
        _signal(
            "WX 1",
            source="wechat",
            published_at="2026-08-13T00:10:00Z",
            watchlist=True,
        ),
        _signal(
            "WX 2",
            source="wechat",
            published_at="2026-08-13T00:11:00Z",
            watchlist=True,
        ),
        *[
            _signal(
                f"HN {index}",
                published_at=f"2026-08-13T00:{20 + index}:00Z",
            )
            for index in range(3)
        ],
        _evidence(
            "Repo lane",
            source="github",
            published_at="2026-08-12T00:00:00Z",
            updated_at="2026-08-13T00:45:00Z",
        ),
        _evidence(
            "Paper lane",
            source="papers",
            published_at="2026-08-13T00:40:00Z",
        ),
    ]
    for index, item in enumerate(items):
        write_research_item(
            item,
            tmp_path / item.source / str(index) / "research-item.json",
        )
    config = DiscoveryConfig(
        output_root=tmp_path,
        log_dir=tmp_path / "logs",
        sources=SourceConfig(
            github=GitHubSource(enabled=True, repos=["example/repo"]),
            papers=PapersSource(enabled=True, categories=["cs.AI"]),
            wechat=WeChatSource(
                enabled=True,
                accounts=[WeChatAccount(name="架构师", wechat_id="JiaGouX")],
            ),
            hackernews=HackerNewsSource(enabled=True, feeds=["newstories"]),
        ),
        briefing=BriefingConfig(
            mode="signals",
            sources=["wechat", "hackernews", "github", "papers"],
            freshness_hours=48,
            hackernews_items=3,
            wechat_min_items=2,
            wechat_max_items=2,
            github_items=1,
            paper_items=1,
            quota_mode=True,
        ),
    )
    reports = {
        name: SourceReport(name=name, enabled=True, succeeded=1)
        for name in ("wechat", "hackernews", "github", "papers")
    }

    artifact = generate_briefing(config, now=now, source_reports=reports)

    assert artifact is not None and artifact.path is not None
    assert artifact.item_count == 7
    assert artifact.status == "ready"
    markdown = artifact.path.read_text(encoding="utf-8")
    assert "## arXiv" in markdown
    assert "## GitHub" in markdown
    assert "## Hacker News" in markdown
    assert "| WeChat minimum | 2 | 2 | 0 |" in markdown


@pytest.mark.parametrize(
    ("case", "briefing_sources", "item_source", "reports", "expected_status"),
    [
        (
            "hn-with-optional-wechat-failure",
            ["hackernews", "wechat"],
            "hackernews",
            {"hackernews": (1, 0), "wechat": (0, 1)},
            "ready",
        ),
        (
            "quiet-hn-with-optional-wechat-failure",
            ["hackernews", "wechat"],
            None,
            {"hackernews": (1, 0), "wechat": (0, 1)},
            "no_fresh_signals",
        ),
        (
            "cached-wechat-with-only-provider-failure",
            ["wechat"],
            "wechat",
            {"wechat": (0, 1)},
            "partial",
        ),
        (
            "empty-with-only-provider-failure",
            ["wechat"],
            None,
            {"wechat": (0, 1)},
            "coverage_incomplete",
        ),
        (
            "x-failure-remains-visible",
            ["hackernews", "wechat", "x"],
            "hackernews",
            {"hackernews": (1, 0), "wechat": (0, 1), "x": (0, 1)},
            "partial",
        ),
    ],
)
def test_generate_quota_briefing_applies_optional_wechat_outcome_matrix(
    tmp_path: Path,
    case: str,
    briefing_sources: list[str],
    item_source: str | None,
    reports: dict[str, tuple[int, int]],
    expected_status: str,
) -> None:
    from research.discovery import (
        BriefingConfig,
        DiscoveryConfig,
        HackerNewsSource,
        SourceConfig,
        WeChatAccount,
        WeChatSource,
        XSource,
    )
    from research.discovery.models import SourceReport
    from research.discovery.runner import generate_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    output_root = tmp_path / case
    if item_source is not None:
        item = _signal(
            f"Fresh {item_source}",
            source=item_source,
            published_at="2026-08-13T00:30:00Z",
        )
        write_research_item(
            item,
            output_root / item_source / "item" / "research-item.json",
        )
    config = DiscoveryConfig(
        output_root=output_root,
        log_dir=output_root / "logs",
        sources=SourceConfig(
            wechat=WeChatSource(
                enabled="wechat" in briefing_sources,
                accounts=[WeChatAccount(name="架构师", wechat_id="JiaGouX")],
            ),
            hackernews=HackerNewsSource(
                enabled="hackernews" in briefing_sources,
                feeds=["newstories"],
            ),
            x=XSource(
                enabled="x" in briefing_sources,
                queries=["agent"],
            ),
        ),
        briefing=BriefingConfig(
            mode="signals",
            sources=briefing_sources,
            hackernews_items=1,
            wechat_min_items=0,
            wechat_max_items=1,
            github_items=0,
            paper_items=0,
            quota_mode=True,
        ),
    )
    source_reports = {
        name: SourceReport(
            name=name,
            enabled=True,
            succeeded=succeeded,
            failed=failed,
            notes=["fixture failure"] if failed else [],
        )
        for name, (succeeded, failed) in reports.items()
    }

    artifact = generate_briefing(config, now=now, source_reports=source_reports)

    assert artifact is not None and artifact.path is not None
    assert artifact.status == expected_status
    markdown = artifact.path.read_text(encoding="utf-8")
    if reports.get("wechat", (0, 0))[1]:
        assert "fixture failure" in markdown
    if case == "x-failure-remains-visible":
        assert "attempted source failed: x" in markdown


def test_legacy_max_items_runner_keeps_one_fresh_news_item_ready(
    tmp_path: Path,
) -> None:
    from research.discovery import load_config
    from research.discovery.models import SourceReport
    from research.discovery.runner import generate_briefing

    config_path = tmp_path / "legacy.yaml"
    config_path.write_text(
        f"""
output_root: {tmp_path / 'output'}
log_dir: {tmp_path / 'logs'}
sources:
  github: {{enabled: false}}
  papers: {{enabled: false}}
  wechat: {{enabled: false}}
  hackernews: {{enabled: true, feeds: [newstories]}}
  x: {{enabled: false}}
briefing:
  mode: signals
  sources: [hackernews]
  freshness_hours: 48
  max_items: 5
limits: {{}}
""",
        encoding="utf-8",
    )
    config = load_config(config_path)
    item = _signal("One is enough", published_at="2026-08-13T00:30:00Z")
    write_research_item(
        item,
        config.output_root / "hackernews" / "one" / "research-item.json",
    )

    artifact = generate_briefing(
        config,
        now=datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc),
        source_reports={
            "hackernews": SourceReport(
                name="hackernews", enabled=True, succeeded=1
            )
        },
    )

    assert artifact is not None and artifact.status == "ready"
    assert artifact.item_count == 1
    assert artifact.path is not None
    markdown = artifact.path.read_text(encoding="utf-8")
    assert "## Top Signals" in markdown
    assert "## Quota Coverage" not in markdown


def test_runner_counts_attempted_failure_outside_briefing_sources_as_partial(
    tmp_path: Path,
) -> None:
    from research.discovery import (
        BriefingConfig,
        DiscoveryConfig,
        GitHubSource,
        HackerNewsSource,
        PapersSource,
        SourceConfig,
        WeChatSource,
        XSource,
    )
    from research.discovery.models import SourceReport
    from research.discovery.runner import generate_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    items = [
        _signal("News", published_at="2026-08-13T00:30:00Z"),
        _evidence(
            "Repo",
            source="github",
            published_at="2026-08-12T00:00:00Z",
            updated_at="2026-08-13T00:40:00Z",
        ),
        _evidence(
            "Paper",
            source="papers",
            published_at="2026-08-13T00:35:00Z",
        ),
    ]
    for index, item in enumerate(items):
        write_research_item(
            item,
            tmp_path / item.source / str(index) / "research-item.json",
        )
    config = DiscoveryConfig(
        output_root=tmp_path,
        log_dir=tmp_path / "logs",
        sources=SourceConfig(
            github=GitHubSource(enabled=True, repos=["example/repo"]),
            papers=PapersSource(enabled=True, categories=["cs.AI"]),
            wechat=WeChatSource(enabled=False),
            hackernews=HackerNewsSource(enabled=True, feeds=["newstories"]),
            x=XSource(enabled=True, queries=["agent"], limit=10),
        ),
        briefing=BriefingConfig(
            mode="signals",
            sources=["hackernews", "github", "papers"],
            hackernews_items=1,
            wechat_min_items=0,
            wechat_max_items=1,
            github_items=1,
            paper_items=1,
            quota_mode=True,
        ),
    )
    reports = {
        source: SourceReport(name=source, enabled=True, succeeded=1)
        for source in ("hackernews", "github", "papers")
    }
    reports["x"] = SourceReport(
        name="x", enabled=True, failed=1, notes=["credential rejected"]
    )

    artifact = generate_briefing(config, now=now, source_reports=reports)

    assert artifact is not None and artifact.status == "partial"
    assert artifact.item_count == 3
    assert artifact.path is not None
    assert "attempted source failed: x" in artifact.path.read_text(encoding="utf-8")


def test_run_discovery_isolates_missing_x_token_and_keeps_hn_signal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import collect.hackernews as hackernews
    from library.items import write_research_items_jsonl
    from research.discovery import (
        BriefingConfig,
        DiscoveryConfig,
        GitHubSource,
        HackerNewsSource,
        PapersSource,
        SourceConfig,
        WeChatSource,
        XSource,
        run_discovery,
    )

    def _fixture_hn(feed: str, *, output_dir: Path, **_kwargs) -> Path:
        feed_dir = output_dir / feed
        path = feed_dir / "signals.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# fixture", encoding="utf-8")
        write_research_items_jsonl(
            [
                _signal(
                    "HN survives",
                    published_at=(datetime.now(timezone.utc) - timedelta(hours=1))
                    .isoformat()
                    .replace("+00:00", "Z"),
                )
            ],
            feed_dir / "research-items.jsonl",
        )
        return path

    monkeypatch.setattr(hackernews, "collect_feed", _fixture_hn)
    monkeypatch.delenv("MISSING_X_TOKEN", raising=False)
    config = DiscoveryConfig(
        output_root=tmp_path / "output",
        log_dir=tmp_path / "logs",
        sources=SourceConfig(
            github=GitHubSource(enabled=False),
            papers=PapersSource(enabled=False),
            wechat=WeChatSource(enabled=False),
            hackernews=HackerNewsSource(
                enabled=True, feeds=["newstories"], keywords=[], limit=10
            ),
            x=XSource(
                enabled=True,
                queries=["agent"],
                token_env="MISSING_X_TOKEN",
                limit=10,
            ),
        ),
        briefing=BriefingConfig(
            mode="signals",
            sources=["hackernews", "x"],
            freshness_hours=48,
            max_items=5,
            quota_mode=False,
        ),
    )

    report = run_discovery(config, only=["hackernews", "x"])

    assert report.sources["hackernews"].succeeded == 1
    assert report.sources["x"].failed == 1
    assert report.briefing is not None
    assert report.briefing.status == "partial"
    assert report.briefing.path is not None
    markdown = report.briefing.path.read_text(encoding="utf-8")
    assert "HN survives" in markdown
    assert "MISSING_X_TOKEN" in markdown


def test_discover_help_lists_realtime_sources_without_standalone_collect(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from research.cli import main

    with pytest.raises(SystemExit) as discover_help:
        main(["discover", "--help"])
    assert discover_help.value.code == 0
    assert "github|papers|wechat|hackernews|x" in capsys.readouterr().out

    with pytest.raises(SystemExit) as collect_help:
        main(["collect", "--help"])
    assert collect_help.value.code == 0
    output = capsys.readouterr().out
    assert "{github,papers,wechat}" in output
    assert "hackernews" not in output and "x}" not in output


def test_github_search_is_recency_evidence_and_returns_real_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import collect.github as github
    from library.storage import load_research_items
    from research.discovery.sources import _github_search_repos

    captured: list[str] = []
    monkeypatch.setattr(
        github,
        "run_gh",
        lambda cmd: captured.extend(cmd)
        or json.dumps(
            [
                {
                    "name": "fresh",
                    "owner": {"login": "example"},
                    "description": "fresh repo",
                    "url": "https://github.com/example/fresh",
                    "stargazersCount": 1,
                    "createdAt": "2026-08-12T00:00:00Z",
                    "updatedAt": "2026-08-13T00:00:00Z",
                }
            ]
        ),
    )

    repos = _github_search_repos("agent", 5, None)
    path = github.save_search_results("agent", tmp_path, repos)

    assert captured[captured.index("--sort") + 1] == "updated"
    assert "createdAt" in captured[captured.index("--json") + 1]
    assert path.is_file()
    item = load_research_items(tmp_path)[0]
    assert item.signal_role == "evidence"
    assert item.published_at == "2026-08-12T00:00:00Z"
    assert item.updated_at == "2026-08-13T00:00:00Z"
