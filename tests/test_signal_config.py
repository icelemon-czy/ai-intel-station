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


def test_load_config_accepts_realtime_sources_and_signal_defaults(tmp_path: Path) -> None:
    from ai_intel_station.discovery import load_config

    config_path = tmp_path / "discovery.yaml"
    config_path.write_text(
        """
sources:
  github:
    enabled: true
    repos: [example/agent]
  papers:
    enabled: true
    categories: [cs.AI]
  wechat:
    enabled: true
    accounts:
      - {name: 架构师, wechat_id: JiaGouX}
    index_limit: 8
  hackernews:
    enabled: true
    feeds: [newstories, showstories]
    keywords: [agent, llm]
    limit: 20
  x:
    enabled: true
    queries: ['agent lang:en -is:retweet']
    token_env: X_BEARER_TOKEN
    limit: 10
briefing: {}
limits: {}
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.sources.wechat.accounts[0].name == "架构师"
    assert config.sources.wechat.accounts[0].wechat_id == "JiaGouX"
    assert config.sources.hackernews.feeds == ["newstories", "showstories"]
    assert config.sources.hackernews.keywords == ["agent", "llm"]
    assert config.sources.x.token_env == "X_BEARER_TOKEN"
    assert config.briefing.mode == "signals"
    assert config.briefing.freshness_hours == 48
    assert config.briefing.quota_mode is True
    assert config.briefing.hackernews_items == 3
    assert config.briefing.wechat_min_items == 0
    assert config.briefing.wechat_max_items == 2
    assert config.briefing.x_items == 0
    assert config.briefing.github_items == 1
    assert config.briefing.paper_items == 1


def test_signal_config_legacy_cap_and_new_quota_conflict(tmp_path: Path) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    legacy_path = tmp_path / "legacy.yaml"
    legacy_path.write_text(
        """
sources:
  github: {enabled: false}
  papers: {enabled: false}
  wechat: {enabled: false}
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false}
briefing:
  mode: signals
  sources: [hackernews]
  max_items: 5
limits: {}
""",
        encoding="utf-8",
    )

    legacy = load_config(legacy_path).briefing
    assert legacy.quota_mode is False
    assert legacy.max_items == 5
    assert legacy.hackernews_items == 5
    assert legacy.wechat_min_items == 0
    assert legacy.wechat_max_items == 5
    assert legacy.github_items == 0
    assert legacy.paper_items == 0

    conflict_path = tmp_path / "conflict.yaml"
    conflict_path.write_text(
        legacy_path.read_text(encoding="utf-8").replace(
            "  max_items: 5", "  max_items: 5\n  news_items: 5"
        ),
        encoding="utf-8",
    )
    with pytest.raises(DiscoveryConfigError, match="max_items"):
        load_config(conflict_path)

    max_conflict_path = tmp_path / "max-conflict.yaml"
    max_conflict_path.write_text(
        legacy_path.read_text(encoding="utf-8").replace(
            "  max_items: 5", "  max_items: 5\n  wechat_max_items: 2"
        ),
        encoding="utf-8",
    )
    with pytest.raises(DiscoveryConfigError, match="max_items"):
        load_config(max_conflict_path)

    github_news_ignored = tmp_path / "github-news-ignored.yaml"
    github_news_ignored.write_text(
        legacy_path.read_text(encoding="utf-8").replace(
            "  max_items: 5", "  max_items: 5\n  github_news_max_items: 1"
        ),
        encoding="utf-8",
    )
    ignored = load_config(github_news_ignored).briefing
    assert ignored.quota_mode is False
    assert ignored.max_items == 5


@pytest.mark.parametrize(
    ("briefing", "needle"),
    [
        ("news_items: 0", "news_items"),
        (
            "news_items: 5\n  wechat_min_items: 3\n  wechat_max_items: 2",
            "wechat_min_items",
        ),
        ("hackernews_items: 10\n  github_items: 6\n  paper_items: 5\n  wechat_max_items: 2", "total"),
    ],
)
def test_signal_config_rejects_invalid_quota_relations(
    tmp_path: Path, briefing: str, needle: str
) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        f"""
sources:
  github: {{enabled: true, repos: [example/agent]}}
  papers: {{enabled: true, categories: [cs.AI]}}
  wechat:
    enabled: true
    accounts: [{{name: 架构师, wechat_id: JiaGouX}}]
  hackernews: {{enabled: true, feeds: [newstories]}}
  x: {{enabled: false}}
briefing:
  mode: signals
  sources: [wechat, hackernews, github, papers]
  {briefing}
limits: {{}}
""",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError, match=needle):
        load_config(config_path)


def test_existing_news_items_migrates_and_github_destination_field_is_ignored(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import load_config

    quota_path = tmp_path / "quota.yaml"
    quota_path.write_text(
        """
sources:
  github: {enabled: false}
  papers: {enabled: false}
  wechat: {enabled: false}
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false}
briefing:
  mode: signals
  sources: [hackernews]
  news_items: 5
  github_news_max_items: 1
  github_items: 0
  paper_items: 0
limits: {}
""",
        encoding="utf-8",
    )
    quota = load_config(quota_path).briefing
    assert quota.quota_mode is True
    assert quota.hackernews_items == 5
    assert quota.wechat_max_items == 2

    generic_path = tmp_path / "generic.yaml"
    generic_path.write_text(
        """
sources: {}
briefing:
  mode: reading-list
  github_news_max_items: not-an-integer
limits: {}
""",
        encoding="utf-8",
    )
    generic = load_config(generic_path).briefing
    assert generic.mode == "reading-list"
    assert generic.hackernews_items == 0


def test_signal_config_preserves_explicit_legacy_wechat_minimum_without_maximum(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import load_config

    config_path = tmp_path / "legacy-wechat-minimum.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: false}
  papers: {enabled: false}
  wechat:
    enabled: true
    accounts: [{name: 架构师, wechat_id: JiaGouX}]
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false}
briefing:
  mode: signals
  sources: [wechat, hackernews]
  news_items: 5
  wechat_min_items: 2
  github_items: 0
  paper_items: 0
limits: {}
""",
        encoding="utf-8",
    )

    briefing = load_config(config_path).briefing

    assert briefing.wechat_min_items == 2
    assert briefing.wechat_max_items == 5


def test_signal_config_does_not_expand_explicit_zero_wechat_minimum(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import load_config

    config_path = tmp_path / "explicit-zero-wechat-minimum.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: false}
  papers: {enabled: false}
  wechat: {enabled: false}
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false}
briefing:
  mode: signals
  sources: [hackernews]
  news_items: 5
  wechat_min_items: 0
  github_items: 0
  paper_items: 0
limits: {}
""",
        encoding="utf-8",
    )

    briefing = load_config(config_path).briefing

    assert briefing.wechat_min_items == 0
    assert briefing.wechat_max_items == 2


def test_optional_wechat_maximum_does_not_require_a_wechat_source(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import load_config

    config_path = tmp_path / "optional-wechat-without-source.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: false}
  papers: {enabled: false}
  wechat: {enabled: false, accounts: []}
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false}
briefing:
  mode: signals
  sources: [hackernews]
  news_items: 5
  wechat_min_items: 0
  wechat_max_items: 2
  github_items: 0
  paper_items: 0
limits: {}
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.sources.wechat.enabled is False
    assert config.briefing.sources == ["hackernews"]
    assert config.briefing.wechat_min_items == 0
    assert config.briefing.wechat_max_items == 2


def test_signal_config_rejects_positive_quota_without_viable_sources(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "missing-sources.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: true, repos: []}
  papers: {enabled: false, categories: []}
  wechat: {enabled: false, accounts: []}
  hackernews: {enabled: false, feeds: []}
  x: {enabled: false, queries: []}
briefing:
  mode: signals
  sources: [hackernews]
  news_items: 5
  wechat_min_items: 2
  github_items: 1
  paper_items: 1
limits: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError) as caught:
        load_config(config_path)
    message = str(caught.value)
    assert "briefing.github_items" in message
    assert "briefing.paper_items" in message
    assert "briefing.wechat_min_items" in message
    assert "briefing.hackernews_items" in message
    assert message.count("•") >= 4


def test_signal_config_rejects_explicit_empty_briefing_sources(
    tmp_path: Path,
) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "empty-sources.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: true, repos: [example/agent]}
  papers: {enabled: true, categories: [cs.AI]}
  wechat:
    enabled: true
    accounts: [{name: 架构师, wechat_id: JiaGouX}]
  hackernews: {enabled: true, feeds: [newstories]}
  x: {enabled: false, queries: []}
briefing:
  mode: signals
  sources: []
  news_items: 5
  wechat_min_items: 2
  github_items: 1
  paper_items: 1
limits: {}
""",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError) as caught:
        load_config(config_path)
    message = str(caught.value)
    assert "briefing.github_items" in message
    assert "briefing.paper_items" in message
    assert "briefing.wechat_min_items" in message
    assert "briefing.hackernews_items" in message


@pytest.mark.parametrize(
    "field",
    ["news_items: 2.9", "max_items: 5.9", "news_items: true"],
)
def test_signal_config_rejects_non_integer_quota_types(
    tmp_path: Path, field: str
) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "non-integer.yaml"
    config_path.write_text(
        f"""
sources:
  github: {{enabled: true, repos: [example/agent]}}
  papers: {{enabled: true, categories: [cs.AI]}}
  wechat:
    enabled: true
    accounts: [{{name: 架构师, wechat_id: JiaGouX}}]
  hackernews: {{enabled: true, feeds: [newstories]}}
  x: {{enabled: false, queries: []}}
briefing:
  mode: signals
  sources: [wechat, hackernews, github, papers]
  {field}
limits: {{}}
""",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError, match="integer"):
        load_config(config_path)


def test_digest_mode_ignores_signal_quota_source_requirements(tmp_path: Path) -> None:
    from ai_intel_station.discovery import load_config

    config_path = tmp_path / "digest.yaml"
    config_path.write_text(
        """
sources:
  github: {enabled: false, repos: []}
  papers: {enabled: false, categories: []}
  wechat: {enabled: false, accounts: []}
  hackernews: {enabled: false, feeds: []}
  x: {enabled: false, queries: []}
briefing:
  mode: digest
  sources: [github]
  news_items: 5
  wechat_min_items: 2
  github_items: 1
  paper_items: 1
limits: {}
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    assert config.briefing.mode == "digest"
    assert config.briefing.quota_mode is False


@pytest.mark.parametrize(
    ("yaml_fragment", "needle"),
    [
        ("wechat:\n    enabled: true\n    accounts: [bad]", "sources.wechat.accounts[0]"),
        ("hackernews:\n    enabled: true\n    feeds: [unknown]", "sources.hackernews.feeds"),
        ("x:\n    enabled: true\n    queries: [agent]\n    token_env: bad-token", "sources.x.token_env"),
    ],
)
def test_load_config_rejects_invalid_realtime_source_shapes(
    tmp_path: Path, yaml_fragment: str, needle: str
) -> None:
    from ai_intel_station.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "discovery.yaml"
    config_path.write_text(
        f"sources:\n  github: {{enabled: false}}\n  papers: {{enabled: false}}\n  {yaml_fragment}\nbriefing: {{}}\nlimits: {{}}\n",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError, match=needle.replace("[", r"\[").replace("]", r"\]")):
        load_config(config_path)


