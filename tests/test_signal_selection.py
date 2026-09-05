from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest

from ai_intel_station.library.items import ResearchItem, write_research_item


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

def test_evidence_cannot_seed_top_list_but_can_raise_corroboration() -> None:
    from ai_intel_station.briefing.signals import select_daily_signals

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    evidence_only = _evidence("Old giant repo")
    evidence_only.metadata["stargazer_count"] = 999999
    single = _signal("New runtime", published_at="2026-08-13T00:30:00Z")
    matching_evidence = _evidence("New runtime", source="papers")

    selected = select_daily_signals(
        [evidence_only, single, matching_evidence],
        now=now,
        freshness_hours=48,
        max_items=5,
    )

    assert [entry.title for entry in selected] == ["New runtime"]
    assert selected[0].confidence == "medium"
    assert [item.source for item in selected[0].evidence] == ["papers"]


def test_quota_selector_builds_source_grouped_default_composition() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    items = [
        _signal(
            "wechat one",
            source="wechat",
            published_at="2026-08-13T00:10:00Z",
            watchlist=True,
        ),
        _signal(
            "wechat two",
            source="wechat",
            published_at="2026-08-12T23:50:00Z",
            watchlist=True,
        ),
        *[
            _signal(
                f"news {index}",
                published_at=f"2026-08-13T00:{20 + index:02d}:00Z",
                engagement=100 - index,
            )
            for index in range(3)
        ],
        _evidence(
            "fresh repo",
            source="github",
            published_at="2026-08-12T12:00:00Z",
            updated_at="2026-08-13T00:45:00Z",
        ),
        _evidence(
            "fresh paper",
            source="papers",
            published_at="2026-08-13T00:40:00Z",
        ),
    ]

    selection = select_daily_briefing(
        items,
        now=now,
        freshness_hours=48,
        hackernews_items=3,
        wechat_min_items=0,
        wechat_max_items=2,
        github_items=1,
        paper_items=1,
    )

    assert len(selection.hackernews) == 3
    assert selection.actual_wechat == 2
    assert [entry.title for entry in selection.github] == ["fresh repo"]
    assert [entry.title for entry in selection.papers] == ["fresh paper"]
    assert len(selection.entries) == 7
    assert selection.has_quota_shortfall is False


def test_optional_wechat_cap_uses_non_wechat_replacements() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    wechat = [
        _signal(
            f"wechat {index}",
            source="wechat",
            published_at=f"2026-08-13T00:{50 - index:02d}:00Z",
            watchlist=True,
        )
        for index in range(4)
    ]
    hackernews = [
        _signal(
            f"hn {index}",
            published_at=f"2026-08-13T00:{30 - index:02d}:00Z",
        )
        for index in range(3)
    ]

    selection = select_daily_briefing(
        [*wechat, *hackernews],
        now=now,
        hackernews_items=3,
        wechat_min_items=0,
        wechat_max_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.hackernews) == 3
    assert selection.actual_wechat == 2
    assert {entry.title for entry in selection.hackernews if entry.title.startswith("hn ")} == {
        "hn 0",
        "hn 1",
        "hn 2",
    }
    assert selection.missing == {}


def test_optional_wechat_cap_can_leave_news_quota_short() -> None:
    from ai_intel_station.briefing.signal_rendering import render_daily_signal_markdown
    from ai_intel_station.briefing.signals import select_daily_briefing
    from ai_intel_station.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [
            _signal(
                f"wechat {index}",
                source="wechat",
                published_at=f"2026-08-13T00:{10 + index:02d}:00Z",
            )
            for index in range(5)
        ],
        now=now,
        hackernews_items=3,
        wechat_min_items=0,
        wechat_max_items=2,
        github_items=0,
        paper_items=0,
    )

    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        {"wechat": SourceReport(name="wechat", enabled=True, succeeded=1)},
        now=now,
        coverage_sources=["wechat"],
        viable_news_sources=["wechat"],
        optional_sources=["wechat"],
    )

    assert len(selection.hackernews) == 0
    assert selection.actual_wechat == 2
    assert selection.missing == {"hackernews": 3}
    assert rendered.status == "partial"
    assert "WeChat optional maximum: 2/2" in rendered.markdown


def test_hackernews_github_targets_stay_in_hackernews() -> None:
    from ai_intel_station.briefing.signal_rendering import render_daily_signal_markdown
    from ai_intel_station.briefing.signals import select_daily_briefing
    from ai_intel_station.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    candidates = [
        _signal(
            "GitHub high",
            url="https://github.com/example/high",
            published_at="2026-08-13T00:50:00Z",
            engagement=100,
        ),
        _signal(
            "GitHub skipped one",
            url="https://github.com/example/skipped-one",
            published_at="2026-08-13T00:49:00Z",
            engagement=90,
        ),
        _signal(
            "Article 0",
            url="https://news.example.com/article-0",
            published_at="2026-08-13T00:40:00Z",
            engagement=70,
        ),
    ]
    selection = select_daily_briefing(
        candidates,
        now=now,
        hackernews_items=3,
        wechat_max_items=0,
        github_items=0,
        paper_items=0,
    )
    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        {"hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1)},
        now=now,
        coverage_sources=["hackernews"],
        viable_news_sources=["hackernews"],
    )
    assert [entry.title for entry in selection.hackernews] == [
        "GitHub high",
        "GitHub skipped one",
        "Article 0",
    ]
    assert all(entry.lane == "hackernews" for entry in selection.hackernews)
    assert selection.github == []
    assert rendered.status == "ready"
    assert "## Hacker News" in rendered.markdown
    assert "GitHub destinations" not in rendered.markdown


def test_cross_source_duplicate_leaves_distinct_hackernews_item() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    shared = "https://github.com/example/shared"
    selection = select_daily_briefing(
        [
            _evidence(
                "Shared repo",
                source="github",
                url=shared,
                published_at="2026-08-12T12:00:00Z",
                updated_at="2026-08-13T00:45:00Z",
            ),
            _signal(
                "Shared repo",
                url=shared,
                published_at="2026-08-13T00:50:00Z",
            ),
            _signal(
                "Distinct repo signal",
                url="https://github.com/example/distinct",
                published_at="2026-08-13T00:40:00Z",
            ),
        ],
        now=now,
        hackernews_items=1,
        github_items=1,
        paper_items=0,
    )
    assert [entry.title for entry in selection.github] == ["Shared repo"]
    assert [item.source for item in selection.github[0].signals] == ["hackernews"]
    assert [entry.title for entry in selection.hackernews] == ["Distinct repo signal"]


def test_legacy_signal_selector_keeps_multiple_github_destinations() -> None:
    from ai_intel_station.briefing.signals import select_daily_signals

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selected = select_daily_signals(
        [
            _signal(
                f"Legacy repo {index}",
                url=f"https://github.com/example/legacy-{index}",
                published_at=f"2026-08-13T00:{50 - index:02d}:00Z",
            )
            for index in range(2)
        ],
        now=now,
        max_items=2,
    )

    assert len(selected) == 2


def test_wechat_minimum_counts_deduped_news_entries_and_reports_shortfall() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    duplicate_a = _signal(
        "Same WeChat",
        source="wechat",
        url="https://example.com/wx?utm_source=one",
        published_at="2026-08-13T00:10:00Z",
        watchlist=True,
    )
    duplicate_b = _signal(
        "same wechat!",
        source="wechat",
        url="https://example.com/wx",
        published_at="2026-08-13T00:20:00Z",
        watchlist=True,
    )
    others = [
        _signal(
            f"HN {index}",
            published_at=f"2026-08-13T00:{30 + index:02d}:00Z",
        )
        for index in range(4)
    ]

    selection = select_daily_briefing(
        [duplicate_a, duplicate_b, *others],
        now=now,
        hackernews_items=3,
        wechat_min_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.hackernews) == 3
    assert selection.actual_wechat == 1
    assert selection.missing == {"wechat": 1}
    assert selection.has_quota_shortfall is True


def test_wechat_minimum_counts_duplicate_and_separate_mixed_group_once_each() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    first_url = "https://example.com/wechat-one"
    mixed_url = "https://example.com/wechat-mixed"
    items = [
        _signal(
            "Wechat one",
            source="wechat",
            url=first_url,
            published_at="2026-08-13T00:10:00Z",
        ),
        _signal(
            "wechat one!",
            source="wechat",
            url=first_url + "?utm_source=duplicate",
            published_at="2026-08-13T00:11:00Z",
        ),
        _signal(
            "Mixed group",
            source="wechat",
            url=mixed_url,
            published_at="2026-08-13T00:20:00Z",
        ),
        _signal(
            "mixed group!",
            source="hackernews",
            url=mixed_url + "?utm_source=hn",
            published_at="2026-08-13T00:21:00Z",
        ),
    ]

    selection = select_daily_briefing(
        items,
        now=now,
        hackernews_items=2,
        wechat_min_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.hackernews) == 1
    assert selection.actual_wechat == 1
    assert len(selection.hackernews[0].signals) == 2
    assert len(selection.wechat[0].signals) == 2
    assert selection.missing == {"hackernews": 1, "wechat": 1}
    assert selection.has_quota_shortfall is True


def test_dedicated_freshness_ranking_and_cross_lane_ownership() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    shared_url = "https://example.com/shared"
    paper = _evidence(
        "Shared launch",
        source="papers",
        url=shared_url,
        published_at="2026-08-13T00:40:00Z",
    )
    github_duplicate = _evidence(
        "shared launch!",
        source="github",
        url=shared_url + "?utm_source=github",
        published_at="2026-08-12T00:00:00Z",
        updated_at="2026-08-13T00:50:00Z",
    )
    new_repo = _evidence(
        "Brand new repo",
        source="github",
        published_at="2026-08-12T23:00:00Z",
        updated_at="2026-08-13T00:30:00Z",
    )
    old_popular_repo = _evidence(
        "Old popular repo",
        source="github",
        published_at="2020-01-01T00:00:00Z",
        updated_at="2026-08-13T00:59:00Z",
    )
    old_popular_repo.metadata["stargazer_count"] = 999999
    news_match = _signal(
        "Shared launch",
        source="hackernews",
        url=shared_url,
        published_at="2026-08-13T00:55:00Z",
    )
    replacement_news = _signal(
        "Different news",
        source="hackernews",
        published_at="2026-08-13T00:45:00Z",
    )

    selection = select_daily_briefing(
        [paper, github_duplicate, new_repo, old_popular_repo, news_match, replacement_news],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert [entry.title for entry in selection.papers] == ["Shared launch"]
    assert [entry.title for entry in selection.github] == ["Brand new repo"]
    assert [entry.title for entry in selection.hackernews] == ["Different news"]
    assert selection.papers[0].confidence == "medium"
    assert [item.source for item in selection.papers[0].signals] == ["hackernews"]
    assert sum(entry.canonical_url == shared_url for entry in selection.entries) == 1


def test_paper_github_duplicate_without_replacement_reports_github_shortfall() -> None:
    from ai_intel_station.briefing.signal_rendering import render_daily_signal_markdown
    from ai_intel_station.briefing.signals import select_daily_briefing
    from ai_intel_station.discovery.models import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    shared_url = "https://example.com/only-dedicated"
    selection = select_daily_briefing(
        [
            _evidence(
                "Only dedicated item",
                source="papers",
                url=shared_url,
                published_at="2026-08-13T00:30:00Z",
            ),
            _evidence(
                "only dedicated item!",
                source="github",
                url=shared_url + "?utm_source=github",
                published_at="2026-08-12T00:00:00Z",
                updated_at="2026-08-13T00:40:00Z",
            ),
            _signal(
                "Different news",
                published_at="2026-08-13T00:45:00Z",
            ),
        ],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert [entry.title for entry in selection.papers] == ["Only dedicated item"]
    assert selection.github == []
    assert selection.missing["github"] == 1
    rendered = render_daily_signal_markdown(
        "daily",
        selection,
        {
            source: SourceReport(name=source, enabled=True, succeeded=1)
            for source in ("hackernews", "github", "papers")
        },
        now=now,
        coverage_sources=["hackernews", "github", "papers"],
        required_sources=["github", "papers"],
        viable_news_sources=["hackernews"],
    )
    assert rendered.status == "partial"
    assert "| GitHub | 1 | 0 | 1 |" in rendered.markdown


def test_dedicated_entries_reject_discovered_only_stale_and_future_times() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    discovered_only = _evidence("discovered only", source="papers", published_at="")
    discovered_only.discovered_at = "2026-08-13T00:55:00Z"
    stale = _evidence(
        "stale repo",
        source="github",
        published_at="2020-01-01T00:00:00Z",
        updated_at="2026-08-11T00:59:59Z",
    )
    future = _evidence(
        "future paper",
        source="papers",
        published_at="2026-08-13T01:06:00Z",
    )

    selection = select_daily_briefing(
        [discovered_only, stale, future],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert selection.entries == []
    assert selection.missing == {"papers": 1, "github": 1, "hackernews": 1}


def test_dedicated_source_time_fallback_and_paper_publication_ranking() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    github_fallback = _evidence(
        "GitHub fallback",
        source="github",
        published_at="2026-08-13T00:20:00Z",
        updated_at=None,
    )
    newer_paper = _evidence(
        "Newer paper",
        source="papers",
        published_at="2026-08-13T00:40:00Z",
    )
    older_paper_with_newer_update = _evidence(
        "Older paper",
        source="papers",
        published_at="2026-08-13T00:30:00Z",
        updated_at="2026-08-13T00:59:00Z",
    )
    stale_paper_with_fresh_update = _evidence(
        "Stale paper",
        source="papers",
        published_at="2026-08-10T00:00:00Z",
        updated_at="2026-08-13T00:58:00Z",
    )

    selected = select_daily_briefing(
        [
            github_fallback,
            newer_paper,
            older_paper_with_newer_update,
            stale_paper_with_fresh_update,
        ],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert [entry.title for entry in selected.github] == ["GitHub fallback"]
    assert selected.github[0].timestamp_field == "published_at"
    assert [entry.title for entry in selected.papers] == ["Newer paper"]

    stale_only = select_daily_briefing(
        [stale_paper_with_fresh_update],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=1,
    )
    assert stale_only.papers == []
    assert stale_only.missing["papers"] == 1


def test_dedicated_confidence_uses_independent_signal_sources_and_watchlist() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    url = "https://example.com/corroborated"
    paper = _evidence(
        "Corroborated paper",
        source="papers",
        url=url,
        published_at="2026-08-13T00:20:00Z",
    )
    hn = _signal(
        "Corroborated paper",
        source="hackernews",
        url=url,
        published_at="2026-08-13T00:30:00Z",
    )
    x = _signal(
        "corroborated paper!",
        source="x",
        url=url + "?utm_source=x",
        published_at="2026-08-13T00:40:00Z",
    )

    selection = select_daily_briefing(
        [paper, hn, x],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=1,
    )

    entry = selection.papers[0]
    assert entry.confidence == "high"
    assert "source=papers" in entry.why_now
    assert "timestamp_field=published_at" in entry.why_now
    assert "signal_sources=2" in entry.why_now


def test_dedicated_confidence_covers_low_medium_and_wechat_watchlist_high() -> None:
    from ai_intel_station.briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    papers = [
        _evidence(
            "Low paper",
            source="papers",
            url="https://example.com/low",
            published_at="2026-08-13T00:30:00Z",
        ),
        _evidence(
            "Medium paper",
            source="papers",
            url="https://example.com/medium",
            published_at="2026-08-13T00:31:00Z",
        ),
        _evidence(
            "High paper",
            source="papers",
            url="https://example.com/high",
            published_at="2026-08-13T00:32:00Z",
        ),
    ]
    signals = [
        _signal(
            "Medium paper",
            source="hackernews",
            url="https://example.com/medium",
            published_at="2026-08-13T00:40:00Z",
        ),
        _signal(
            "High paper",
            source="wechat",
            url="https://example.com/high",
            published_at="2026-08-13T00:41:00Z",
            watchlist=True,
        ),
    ]

    selection = select_daily_briefing(
        [*papers, *signals],
        now=now,
        hackernews_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=3,
    )

    confidence = {entry.title: entry.confidence for entry in selection.papers}
    assert confidence == {
        "High paper": "high",
        "Medium paper": "medium",
        "Low paper": "low",
    }


def test_dedupe_normalization_ranking_and_confidence_are_deterministic() -> None:
    from ai_intel_station.briefing.signals import select_daily_signals

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    first = _signal(
        "Agent Runtime!",
        source="hackernews",
        url="https://EXAMPLE.com/runtime/?utm_source=hn#top",
        published_at="2026-08-13T00:30:00Z",
        engagement=10,
    )
    second = _signal(
        "agent runtime",
        source="x",
        url="https://example.com/runtime",
        published_at="2026-08-13T00:40:00Z",
        engagement=9999,
    )
    watchlist = _signal(
        "Watchlist story",
        source="wechat",
        published_at="2026-08-12T23:00:00Z",
        watchlist=True,
        engagement=0,
    )

    selected = select_daily_signals(
        [second, watchlist, first],
        now=now,
        freshness_hours=48,
        max_items=5,
    )

    assert [entry.title for entry in selected] == ["Watchlist story", "Agent Runtime!"]
    assert selected[0].confidence == "medium"
    assert "watchlist=yes" in selected[0].why_now
    assert "engagement_percentile=0.50" in selected[0].why_now
    assert selected[1].confidence == "high"
    assert selected[1].signal_source_count == 2


