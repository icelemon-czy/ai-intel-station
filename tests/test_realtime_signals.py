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


def test_load_config_accepts_realtime_sources_and_signal_defaults(tmp_path: Path) -> None:
    from research.discovery import load_config

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
    assert config.briefing.news_items == 5
    assert config.briefing.wechat_min_items == 0
    assert config.briefing.wechat_max_items == 2
    assert config.briefing.github_news_max_items == 1
    assert config.briefing.github_items == 1
    assert config.briefing.paper_items == 1


def test_signal_config_legacy_cap_and_new_quota_conflict(tmp_path: Path) -> None:
    from research.discovery import DiscoveryConfigError, load_config

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
    assert legacy.news_items == 5
    assert legacy.wechat_min_items == 0
    assert legacy.wechat_max_items == 5
    assert legacy.github_news_max_items is None
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

    github_news_conflict = tmp_path / "github-news-conflict.yaml"
    github_news_conflict.write_text(
        legacy_path.read_text(encoding="utf-8").replace(
            "  max_items: 5", "  max_items: 5\n  github_news_max_items: 1"
        ),
        encoding="utf-8",
    )
    with pytest.raises(DiscoveryConfigError, match="max_items"):
        load_config(github_news_conflict)


@pytest.mark.parametrize(
    ("briefing", "needle"),
    [
        ("news_items: 0", "news_items"),
        ("news_items: 2\n  wechat_max_items: 3", "wechat_max_items"),
        ("news_items: 2\n  github_news_max_items: 3", "github_news_max_items"),
        ("news_items: 5\n  github_news_max_items: true", "github_news_max_items"),
        (
            "news_items: 5\n  wechat_min_items: 3\n  wechat_max_items: 2",
            "wechat_min_items",
        ),
        ("news_items: 10\n  github_items: 6\n  paper_items: 5\n  wechat_min_items: 2", "total"),
    ],
)
def test_signal_config_rejects_invalid_quota_relations(
    tmp_path: Path, briefing: str, needle: str
) -> None:
    from research.discovery import DiscoveryConfigError, load_config

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


def test_github_news_maximum_does_not_require_github_source_and_generic_mode_ignores_it(
    tmp_path: Path,
) -> None:
    from research.discovery import load_config

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
    assert quota.github_news_max_items == 1

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
    assert generic.github_news_max_items is None


def test_signal_config_preserves_explicit_legacy_wechat_minimum_without_maximum(
    tmp_path: Path,
) -> None:
    from research.discovery import load_config

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
    from research.discovery import load_config

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
    from research.discovery import load_config

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
    from research.discovery import DiscoveryConfigError, load_config

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
    assert "briefing.news_items" in message
    assert message.count("•") >= 4


def test_signal_config_rejects_explicit_empty_briefing_sources(
    tmp_path: Path,
) -> None:
    from research.discovery import DiscoveryConfigError, load_config

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
    assert "briefing.news_items" in message


@pytest.mark.parametrize(
    "field",
    ["news_items: 2.9", "max_items: 5.9", "news_items: true"],
)
def test_signal_config_rejects_non_integer_quota_types(
    tmp_path: Path, field: str
) -> None:
    from research.discovery import DiscoveryConfigError, load_config

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
    from research.discovery import load_config

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
    from research.discovery import DiscoveryConfigError, load_config

    config_path = tmp_path / "discovery.yaml"
    config_path.write_text(
        f"sources:\n  github: {{enabled: false}}\n  papers: {{enabled: false}}\n  {yaml_fragment}\nbriefing: {{}}\nlimits: {{}}\n",
        encoding="utf-8",
    )

    with pytest.raises(DiscoveryConfigError, match=needle.replace("[", r"\[").replace("]", r"\]")):
        load_config(config_path)


def test_hackernews_fixture_collection_writes_signal_sidecars(tmp_path: Path) -> None:
    from collect.hackernews import collect_feed
    from library.storage import load_research_items

    payloads = {
        "https://hacker-news.firebaseio.com/v0/newstories.json": [101, 102],
        "https://hacker-news.firebaseio.com/v0/item/101.json": {
            "id": 101,
            "type": "story",
            "title": "New agent runtime",
            "url": "https://example.com/runtime",
            "by": "alice",
            "time": 1786581000,
            "score": 42,
            "descendants": 13,
        },
        "https://hacker-news.firebaseio.com/v0/item/102.json": {
            "id": 102,
            "type": "story",
            "title": "Unrelated database post",
            "url": "https://example.com/db",
            "by": "bob",
            "time": 1786581001,
            "score": 100,
            "descendants": 25,
        },
    }

    path = collect_feed(
        "newstories",
        keywords=["agent"],
        limit=10,
        output_dir=tmp_path,
        request_json=lambda url, **_: payloads[url],
        discovered_at="2026-08-13T01:00:00Z",
    )

    assert path.is_file()
    items = load_research_items(tmp_path)
    assert len(items) == 1
    assert items[0].signal_role == "signal"
    assert items[0].published_at == "2026-08-13T00:30:00Z"
    assert items[0].metadata["discussion_url"] == "https://news.ycombinator.com/item?id=101"
    assert items[0].metadata["engagement_count"] == 55


def test_hackernews_malformed_feed_fails_instead_of_empty_success(tmp_path: Path) -> None:
    from collect.hackernews import HackerNewsFetchError, collect_feed

    with pytest.raises(HackerNewsFetchError, match="newstories"):
        collect_feed(
            "newstories",
            keywords=[],
            limit=10,
            output_dir=tmp_path,
            request_json=lambda *_args, **_kwargs: {"not": "a list"},
        )


def test_hackernews_oversized_and_unavailable_items_fail_with_context(
    tmp_path: Path,
) -> None:
    from collect.hackernews import HackerNewsFetchError, collect_feed

    def _unavailable(url: str, **_kwargs):
        if url.endswith("newstories.json"):
            return [101]
        raise OSError("fixture offline")

    with pytest.raises(HackerNewsFetchError, match=r"newstories item 101"):
        collect_feed(
            "newstories",
            keywords=[],
            limit=10,
            output_dir=tmp_path,
            request_json=_unavailable,
        )

    with pytest.raises(HackerNewsFetchError, match="exceeds"):
        collect_feed(
            "newstories",
            keywords=[],
            limit=10,
            output_dir=tmp_path,
            request_json=lambda url, **_kwargs: (
                (_ for _ in ()).throw(HackerNewsFetchError("response exceeds limit"))
            ),
        )


def test_x_fixture_collection_and_missing_token_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from collect.x import XCredentialError, collect_recent_search
    from library.storage import load_research_items

    requested: list[str] = []
    monkeypatch.setenv("TEST_X_TOKEN", "secret")

    path = collect_recent_search(
        "agent lang:en",
        token_env="TEST_X_TOKEN",
        limit=10,
        output_dir=tmp_path,
        request_json=lambda url, **kwargs: (
            requested.append(url)
            or {
                "data": [
                    {
                        "id": "123",
                        "text": "A new agent launch",
                        "author_id": "42",
                        "created_at": "2026-08-13T00:45:00Z",
                        "public_metrics": {"like_count": 10, "retweet_count": 4, "reply_count": 3},
                    }
                ]
            }
        ),
        discovered_at="2026-08-13T01:00:00Z",
        freshness_hours=48,
        now=datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc),
    )

    assert path.is_file()
    assert "max_results=10" in requested[0]
    params = parse_qs(urlsplit(requested[0]).query)
    assert params["start_time"] == ["2026-08-11T01:00:00Z"]
    assert params["end_time"] == ["2026-08-13T01:00:00Z"]
    item = load_research_items(tmp_path)[0]
    assert item.source == "x"
    assert item.signal_role == "signal"
    assert item.metadata["engagement_count"] == 17

    monkeypatch.delenv("TEST_X_TOKEN")
    called = False

    def _must_not_request(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("request must not run")

    with pytest.raises(XCredentialError, match="TEST_X_TOKEN"):
        collect_recent_search(
            "agent",
            token_env="TEST_X_TOKEN",
            limit=10,
            output_dir=tmp_path,
            request_json=_must_not_request,
        )
    assert called is False


def test_wechat_index_fixture_discovers_watchlist_and_rejects_captcha(tmp_path: Path) -> None:
    from collect.wechat_index import WeChatIndexCoverageError, collect_account
    from library.storage import load_research_items

    html = """
    <ul class="news-list2">
      <li><h3><a href="https://weixin.sogou.com/link?url=abc">Agent 新架构</a></h3>
      <p class="txt-info">一线实践摘要</p><div class="s-p"><span class="all-time-y2">1786581000</span></div>
      <div class="s-p"><a class="account">架构师</a></div></li>
    </ul>
    """

    path = collect_account(
        "架构师",
        "JiaGouX",
        limit=5,
        output_dir=tmp_path,
        request_text=lambda *_args, **_kwargs: html,
        discovered_at="2026-08-13T01:00:00Z",
    )

    assert path.is_file()
    item = load_research_items(tmp_path)[0]
    assert item.source == "wechat"
    assert item.metadata["watchlist"] is True
    assert item.metadata["account"] == "架构师"
    assert item.published_at == "2026-08-13T00:30:00Z"

    with pytest.raises(WeChatIndexCoverageError, match="verification"):
        collect_account(
            "架构师",
            "JiaGouX",
            limit=5,
            output_dir=tmp_path,
            request_text=lambda *_args, **_kwargs: "当前环境异常，完成验证后即可继续访问。",
        )


@pytest.mark.parametrize(
    ("body", "needle"),
    [
        ("", "no attributable"),
        ("<html><li>broken</li></html>", "no attributable"),
        (
            '<li><h3><a href="/link?a=1">Agent</a></h3>'
            '<span class="all-time-y2">1786581000</span></li>',
            "no attributable",
        ),
        (
            '<li><h3><a href="/link?a=1">Agent</a></h3><a class="account">架构师</a></li>',
            "omitted publication time",
        ),
    ],
)
def test_wechat_index_empty_malformed_and_missing_time_are_incomplete(
    tmp_path: Path, body: str, needle: str
) -> None:
    from collect.wechat_index import WeChatIndexCoverageError, collect_account

    with pytest.raises(WeChatIndexCoverageError, match=needle):
        collect_account(
            "架构师",
            "JiaGouX",
            limit=5,
            output_dir=tmp_path,
            request_text=lambda *_args, **_kwargs: body,
        )


def test_repeated_write_preserves_first_discovered_at(tmp_path: Path) -> None:
    sidecar = tmp_path / "research-item.json"
    first = _signal(
        "Same story",
        published_at="2026-08-13T00:00:00Z",
        engagement=1,
    )
    first.discovered_at = "2026-08-13T01:00:00Z"
    write_research_item(first, sidecar)

    later = _signal(
        "Same story",
        published_at="2026-08-13T00:00:00Z",
        engagement=99,
    )
    later.discovered_at = "2026-08-14T01:00:00Z"
    write_research_item(later, sidecar)

    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    assert payload["discovered_at"] == "2026-08-13T01:00:00Z"
    assert payload["metadata"]["engagement_count"] == 99


def test_jsonl_reappearance_preserves_first_observation_across_absent_run(
    tmp_path: Path,
) -> None:
    from library.items import write_research_items_jsonl

    path = tmp_path / "research-items.jsonl"
    first = _signal("Returns later", published_at="2026-08-13T00:00:00Z")
    first.discovered_at = "2026-08-13T01:00:00Z"
    write_research_items_jsonl([first], path)
    write_research_items_jsonl([], path)

    observed_again = _signal(
        "Returns later", published_at="2026-08-13T00:00:00Z", engagement=50
    )
    observed_again.discovered_at = "2026-08-14T01:00:00Z"
    write_research_items_jsonl([observed_again], path)

    payloads = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(payloads) == 1
    assert payloads[0]["discovered_at"] == "2026-08-13T01:00:00Z"
    assert payloads[0]["metadata"]["engagement_count"] == 50


def test_backfilled_legacy_item_does_not_invent_discovered_at() -> None:
    item = ResearchItem(source="papers", item_type="paper", title="Legacy")
    assert item.discovered_at is None
    assert item.signal_role is None


def test_freshness_gate_is_timezone_aware_inclusive_and_rejects_future_skew() -> None:
    from briefing.signals import select_daily_signals

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    items = [
        _signal("boundary", published_at=(now - timedelta(hours=48)).isoformat()),
        _signal("too old", published_at=(now - timedelta(hours=48, seconds=1)).isoformat()),
        _signal("future", published_at=(now + timedelta(minutes=6)).isoformat()),
        _signal("wechat naive", source="wechat", published_at="2026-08-13 08:30:00"),
        _signal("unknown", published_at=""),
    ]

    selected = select_daily_signals(items, now=now, freshness_hours=48, max_items=5)

    assert {entry.title for entry in selected} == {"boundary", "wechat naive"}


def test_evidence_cannot_seed_top_list_but_can_raise_corroboration() -> None:
    from briefing.signals import select_daily_signals

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


def test_quota_selector_builds_five_news_two_wechat_github_and_paper() -> None:
    from briefing.signals import select_daily_briefing

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
                source="hackernews" if index % 2 else "x",
                published_at=f"2026-08-13T00:{20 + index:02d}:00Z",
                engagement=100 - index,
            )
            for index in range(5)
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
        news_items=5,
        wechat_min_items=0,
        wechat_max_items=2,
        github_items=1,
        paper_items=1,
    )

    assert len(selection.news) == 5
    assert selection.actual_wechat == 2
    assert [entry.title for entry in selection.github] == ["fresh repo"]
    assert [entry.title for entry in selection.papers] == ["fresh paper"]
    assert len(selection.entries) == 7
    assert selection.has_quota_shortfall is False


def test_optional_wechat_cap_uses_non_wechat_replacements() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=5,
        wechat_min_items=0,
        wechat_max_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.news) == 5
    assert selection.actual_wechat == 2
    assert {entry.title for entry in selection.news if entry.title.startswith("hn ")} == {
        "hn 0",
        "hn 1",
        "hn 2",
    }
    assert selection.missing == {}


def test_optional_wechat_cap_can_leave_news_quota_short() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=5,
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

    assert len(selection.news) == 2
    assert selection.actual_wechat == 2
    assert selection.missing == {"news": 3}
    assert rendered.status == "partial"
    assert "WeChat optional maximum: 2/2" in rendered.markdown


def test_github_news_cap_uses_replacements_and_reports_exact_exclusions() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
            "GitHub skipped two",
            url="https://github.com/example/skipped-two",
            published_at="2026-08-13T00:48:00Z",
            engagement=80,
        ),
        *[
            _signal(
                f"Article {index}",
                url=f"https://news.example.com/article-{index}",
                published_at=f"2026-08-13T00:{40 - index:02d}:00Z",
                engagement=70 - index,
            )
            for index in range(4)
        ],
        _signal(
            "GitHub below cutoff",
            url="https://github.com/example/below-cutoff",
            published_at="2026-08-13T00:10:00Z",
            engagement=1,
        ),
    ]

    selection = select_daily_briefing(
        candidates,
        now=now,
        news_items=5,
        wechat_min_items=0,
        wechat_max_items=0,
        github_news_max_items=1,
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

    assert [entry.title for entry in selection.news] == [
        "GitHub high",
        "Article 0",
        "Article 1",
        "Article 2",
        "Article 3",
    ]
    assert selection.actual_github_news == 1
    assert selection.excluded_github_news == 2
    assert selection.missing == {}
    assert rendered.status == "ready"
    assert "GitHub destinations in News: 1/1 (excluded by cap: 2)" in rendered.markdown


def test_github_news_cap_shortfall_does_not_bypass_maximum() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [
            _signal(
                f"Repo {index}",
                url=f"https://github.com/example/repo-{index}",
                published_at=f"2026-08-13T00:{50 - index:02d}:00Z",
                engagement=10 - index,
            )
            for index in range(3)
        ],
        now=now,
        news_items=5,
        wechat_min_items=0,
        wechat_max_items=0,
        github_news_max_items=1,
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

    assert len(selection.news) == 1
    assert selection.actual_github_news == 1
    assert selection.excluded_github_news == 2
    assert selection.missing == {"news": 4}
    assert rendered.status == "partial"


def test_cross_lane_duplicate_does_not_consume_github_news_slot() -> None:
    from briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    shared_url = "https://github.com/example/dedicated"
    selection = select_daily_briefing(
        [
            _evidence(
                "Dedicated repo",
                source="github",
                url=shared_url,
                published_at="2026-08-12T23:00:00Z",
                updated_at="2026-08-13T00:55:00Z",
            ),
            _signal(
                "Dedicated repo",
                url=shared_url,
                published_at="2026-08-13T00:50:00Z",
                engagement=10,
            ),
            _signal(
                "Distinct repo signal",
                url="https://github.com/example/distinct",
                published_at="2026-08-13T00:40:00Z",
                engagement=5,
            ),
        ],
        now=now,
        news_items=1,
        github_news_max_items=1,
        github_items=1,
        paper_items=0,
    )

    assert [entry.title for entry in selection.github] == ["Dedicated repo"]
    assert [entry.title for entry in selection.news] == ["Distinct repo signal"]
    assert selection.actual_github_news == 1
    assert selection.excluded_github_news == 0
    assert [item.source for item in selection.github[0].signals] == ["hackernews"]


def test_github_destination_host_boundary_is_exact_after_normalization() -> None:
    from briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    urls = {
        "github exact": "https://GitHub.Com/example/repo",
        "github subdomain": "https://gist.github.com/example/abc",
        "github io": "https://github.io/project",
        "user github io": "https://user.github.io/project",
        "lookalike": "https://notgithub.com/project",
        "evil suffix": "https://github.com.evil.example/project",
    }
    selection = select_daily_briefing(
        [
            _signal(
                title,
                url=url,
                published_at=f"2026-08-13T00:{50 - index:02d}:00Z",
                engagement=20 - index,
            )
            for index, (title, url) in enumerate(urls.items())
        ],
        now=now,
        news_items=6,
        wechat_max_items=0,
        github_news_max_items=0,
        github_items=0,
        paper_items=0,
    )

    assert {entry.title for entry in selection.news} == {
        "github io",
        "user github io",
        "lookalike",
        "evil suffix",
    }
    assert selection.actual_github_news == 0
    assert selection.excluded_github_news == 2


def test_mixed_wechat_github_entries_obey_both_caps_with_replacement() -> None:
    from briefing.signals import select_daily_briefing

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    mixed = [
        _signal(
            f"Mixed {index}",
            source="wechat",
            url=f"https://github.com/example/mixed-{index}",
            published_at=f"2026-08-13T00:{50 - index:02d}:00Z",
            watchlist=True,
        )
        for index in range(2)
    ]
    replacement = _signal(
        "HN replacement",
        url="https://news.example.com/replacement",
        published_at="2026-08-13T00:30:00Z",
    )

    with_replacement = select_daily_briefing(
        [*mixed, replacement],
        now=now,
        news_items=2,
        wechat_min_items=2,
        wechat_max_items=2,
        github_news_max_items=1,
        github_items=0,
        paper_items=0,
    )
    without_replacement = select_daily_briefing(
        mixed,
        now=now,
        news_items=2,
        wechat_min_items=2,
        wechat_max_items=2,
        github_news_max_items=1,
        github_items=0,
        paper_items=0,
    )

    assert len(with_replacement.news) == 2
    assert with_replacement.actual_wechat == 1
    assert with_replacement.actual_github_news == 1
    assert with_replacement.missing == {"wechat": 1}
    assert with_replacement.excluded_github_news == 1
    assert len(without_replacement.news) == 1
    assert without_replacement.missing == {"news": 1, "wechat": 1}
    assert without_replacement.excluded_github_news == 1


def test_zero_github_news_cap_has_honest_empty_and_nonempty_statuses() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    repo_signal = _signal(
        "Repo signal",
        url="https://github.com/example/repo",
        published_at="2026-08-13T00:50:00Z",
    )
    reports = {"hackernews": SourceReport(name="hackernews", enabled=True, succeeded=1)}
    empty_selection = select_daily_briefing(
        [repo_signal],
        now=now,
        news_items=1,
        github_news_max_items=0,
        github_items=0,
        paper_items=0,
    )
    empty_rendered = render_daily_signal_markdown(
        "daily-empty",
        empty_selection,
        reports,
        now=now,
        coverage_sources=["hackernews"],
        viable_news_sources=["hackernews"],
    )
    nonempty_selection = select_daily_briefing(
        [
            repo_signal,
            _evidence(
                "Paper",
                source="papers",
                published_at="2026-08-13T00:40:00Z",
            ),
        ],
        now=now,
        news_items=1,
        github_news_max_items=0,
        github_items=0,
        paper_items=1,
    )
    nonempty_rendered = render_daily_signal_markdown(
        "daily-nonempty",
        nonempty_selection,
        reports,
        now=now,
        coverage_sources=["hackernews"],
        viable_news_sources=["hackernews"],
    )

    assert empty_selection.entries == []
    assert empty_selection.excluded_github_news == 1
    assert empty_rendered.status == "no_fresh_signals"
    assert "1 fresh News candidate(s) excluded by GitHub destination cap" in empty_rendered.markdown
    assert len(nonempty_selection.entries) == 1
    assert nonempty_selection.missing == {"news": 1}
    assert nonempty_rendered.status == "partial"
    assert "1 fresh News candidate(s) excluded by GitHub destination cap" in nonempty_rendered.markdown


def test_legacy_signal_selector_keeps_multiple_github_destinations() -> None:
    from briefing.signals import select_daily_signals

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
    from briefing.signals import select_daily_briefing

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
        news_items=5,
        wechat_min_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.news) == 5
    assert selection.actual_wechat == 1
    assert selection.missing == {"wechat": 1}
    assert selection.has_quota_shortfall is True


def test_wechat_minimum_counts_duplicate_and_separate_mixed_group_once_each() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=2,
        wechat_min_items=2,
        github_items=0,
        paper_items=0,
    )

    assert len(selection.news) == 2
    assert selection.actual_wechat == 2
    assert sorted(len(entry.signals) for entry in selection.news) == [2, 2]
    assert selection.has_quota_shortfall is False


def test_dedicated_freshness_ranking_and_cross_lane_ownership() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert [entry.title for entry in selection.papers] == ["Shared launch"]
    assert [entry.title for entry in selection.github] == ["Brand new repo"]
    assert [entry.title for entry in selection.news] == ["Different news"]
    assert selection.papers[0].confidence == "medium"
    assert [item.source for item in selection.papers[0].signals] == ["hackernews"]
    assert sum(entry.canonical_url == shared_url for entry in selection.entries) == 1


def test_paper_github_duplicate_without_replacement_reports_github_shortfall() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=1,
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
    from briefing.signals import select_daily_briefing

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
        news_items=1,
        wechat_min_items=0,
        github_items=1,
        paper_items=1,
    )

    assert selection.entries == []
    assert selection.missing == {"papers": 1, "github": 1, "news": 1}


def test_dedicated_source_time_fallback_and_paper_publication_ranking() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=1,
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
        news_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=1,
    )
    assert stale_only.papers == []
    assert stale_only.missing["papers"] == 1


def test_dedicated_confidence_uses_independent_signal_sources_and_watchlist() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=1,
        wechat_min_items=0,
        github_items=0,
        paper_items=1,
    )

    entry = selection.papers[0]
    assert entry.confidence == "high"
    assert "lane=papers" in entry.why_now
    assert "timestamp_field=published_at" in entry.why_now
    assert "signal_sources=2" in entry.why_now


def test_dedicated_confidence_covers_low_medium_and_wechat_watchlist_high() -> None:
    from briefing.signals import select_daily_briefing

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
        news_items=1,
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
    from briefing.signals import select_daily_signals

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


def test_renderer_separates_hn_target_from_discussion_and_preserves_other_sources() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=3,
        wechat_max_items=2,
        github_news_max_items=1,
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
            news_items=1,
            github_news_max_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_signals
    from research.discovery.runner import SourceReport

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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=1,
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
    assert "## News" in rendered.markdown
    assert "| WeChat minimum | 1 | 0 | 1 |" in rendered.markdown
    assert "public index unavailable" in rendered.markdown


def test_wechat_quota_shortfall_alone_makes_nonempty_result_partial() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("HN fills News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=1,
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
            news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

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
        news_items=1,
        wechat_min_items=0,
        wechat_max_items=1,
        github_items=0,
        paper_items=0,
    )
    empty_selection = select_daily_briefing(
        [],
        now=now,
        news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("HN fills News", published_at="2026-08-13T00:30:00Z")],
        now=now,
        news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    local_news = _signal("Local sidecar", published_at="2026-08-13T00:30:00Z")
    selection = select_daily_briefing(
        [local_news],
        now=now,
        news_items=1,
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
        news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [_signal("usable", published_at="2026-08-13T00:30:00Z")],
        now=now,
        news_items=1,
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
    from briefing.signals import render_daily_signal_markdown, select_daily_briefing
    from research.discovery.runner import SourceReport

    now = datetime(2026, 8, 13, 1, 0, tzinfo=timezone.utc)
    selection = select_daily_briefing(
        [],
        now=now,
        news_items=1,
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
    assert "| News | 1 | 0 | 1 |" in rendered.markdown


def test_signal_markdown_escapes_untrusted_titles_and_coverage_notes() -> None:
    from briefing.signals import render_daily_signal_markdown, select_daily_signals
    from research.discovery.runner import SourceReport

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
    from briefing.signals import render_daily_signal_markdown, select_daily_signals

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
            news_items=5,
            wechat_min_items=0,
            wechat_max_items=2,
            github_news_max_items=1,
            github_items=1,
            paper_items=1,
            quota_mode=True,
        ),
    )

    with DiscoveryLogger(config.log_dir) as logger:
        artifact = generate_briefing(config, report_log=logger, dry_run=True)

    output = capsys.readouterr().out
    assert artifact is not None and artifact.status == "dry_run"
    assert "GitHub destinations maximum=1" in output
    assert "actual/excluded=unavailable" in output
    assert "GitHub destinations actual=0" not in output


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

    assert config.briefing.github_news_max_items == 0
    assert artifact is not None and artifact.status == "ready"
    markdown = artifact.path.read_text(encoding="utf-8")
    assert "### 1. [External analysis](https://news.example.com/analysis)" in markdown
    assert "GitHub destinations in News: 0/0 (excluded by cap: 2)" in markdown
    assert "Repo launch one" not in markdown
    assert "Repo launch two" not in markdown


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
    from research.discovery.runner import SourceReport, generate_briefing

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
            news_items=5,
            wechat_min_items=2,
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
    assert "## News" in markdown
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
    from research.discovery.runner import SourceReport, generate_briefing

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
            news_items=1,
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
    from research.discovery.runner import SourceReport, generate_briefing

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
    from research.discovery.runner import SourceReport, generate_briefing

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
            news_items=1,
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
    from collect import github
    from library.storage import load_research_items
    from research.discovery.runner import _github_search_repos

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
