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

def test_hackernews_fixture_collection_writes_signal_sidecars(tmp_path: Path) -> None:
    from ai_intel_station.collect.hackernews import collect_feed
    from ai_intel_station.library.storage import load_research_items

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
    from ai_intel_station.collect.hackernews import HackerNewsFetchError, collect_feed

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
    from ai_intel_station.collect.hackernews import HackerNewsFetchError, collect_feed

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
    from ai_intel_station.collect.x import XCredentialError, collect_recent_search
    from ai_intel_station.library.storage import load_research_items

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
    from ai_intel_station.collect.wechat_index import WeChatIndexCoverageError, collect_account
    from ai_intel_station.library.storage import load_research_items

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
    from ai_intel_station.collect.wechat_index import WeChatIndexCoverageError, collect_account

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
    from ai_intel_station.library.items import write_research_items_jsonl

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
    from ai_intel_station.briefing.signals import select_daily_signals

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


