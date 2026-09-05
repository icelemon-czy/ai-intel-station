from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from library.items import ResearchItem


REALTIME_SOURCES = frozenset({"wechat", "hackernews", "x"})
EVIDENCE_SOURCES = frozenset({"github", "papers"})
TRACKING_QUERY_KEYS = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"})


@dataclass
class SelectedSignal:
    title: str
    canonical_url: str | None
    published_at: str
    what: str
    why_now: str
    confidence: str
    signals: list[ResearchItem] = field(default_factory=list)
    evidence: list[ResearchItem] = field(default_factory=list)
    signal_source_count: int = 0
    watchlist: bool = False
    engagement_percentile: float = 0.5
    lane: str = "news"
    timestamp_field: str = "published_at"
    _published_datetime: datetime | None = field(default=None, repr=False)


@dataclass
class RenderedSignalBriefing:
    status: str
    markdown: str


@dataclass
class DailyBriefingSelection:
    papers: list[SelectedSignal] = field(default_factory=list)
    github: list[SelectedSignal] = field(default_factory=list)
    hackernews: list[SelectedSignal] = field(default_factory=list)
    wechat: list[SelectedSignal] = field(default_factory=list)
    x: list[SelectedSignal] = field(default_factory=list)
    expected_hackernews: int = 3
    expected_wechat: int = 0
    max_wechat: int = 2
    expected_x: int = 0
    expected_github: int = 1
    expected_papers: int = 1
    quota_mode: bool = True

    @property
    def entries(self) -> list[SelectedSignal]:
        return [*self.papers, *self.github, *self.hackernews, *self.wechat, *self.x]

    @property
    def actual_wechat(self) -> int:
        return len(self.wechat)

    @property
    def missing(self) -> dict[str, int]:
        if not self.quota_mode:
            return {}
        missing: dict[str, int] = {}
        values = (
            ("papers", self.expected_papers, len(self.papers)),
            ("github", self.expected_github, len(self.github)),
            ("hackernews", self.expected_hackernews, len(self.hackernews)),
            ("wechat", self.expected_wechat, self.actual_wechat),
            ("x", self.expected_x, len(self.x)),
        )
        for name, expected, actual in values:
            if actual < expected:
                missing[name] = expected - actual
        return missing

    @property
    def has_quota_shortfall(self) -> bool:
        return bool(self.missing)
