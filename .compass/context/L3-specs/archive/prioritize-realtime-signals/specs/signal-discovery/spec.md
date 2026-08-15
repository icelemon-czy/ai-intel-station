# Signal Discovery — Archived Delta Spec

> 本文件新增 `specs/signal-discovery/spec.md` capability。

## ADDED Requirements

### Requirement: Realtime Signal Sources

signal discovery SHALL support Hacker News public feeds and X recent search as independently
configured sources; a disabled or unavailable source MUST NOT prevent another source from completing.

#### Scenario: Collect Hacker News signals

- **WHEN** Hacker News source is enabled with feed and keyword preferences
- **THEN**system fetches recent matching stories and saves normalized ResearchItem sidecars
- **AND**each item preserves publication time, discussion link and available score/comment metrics

#### Scenario: Hacker News returns malformed or unavailable data

- **WHEN**a Hacker News feed or item response is unavailable, malformed or exceeds the bounded response limit
- **THEN**Hacker News source reports failure with the affected feed or item context
- **AND**it does not save the malformed response as an empty successful result

#### Scenario: Collect X recent-search signals

- **WHEN**X source is enabled with a valid token environment variable and one or more queries
- **THEN**system requests recent Posts with creation time, author and public metrics and saves normalized signal sidecars
- **AND**the request is bounded by the configured per-query limit and `briefing.freshness_hours`
  expressed as explicit recent-search `start_time` / `end_time`

#### Scenario: X credential is unavailable

- **WHEN** X source is enabled but its configured bearer-token environment variable is absent
- **THEN**X source reports an actionable failure without making a request
- **AND**other independent source and briefing stages continue

### Requirement: Explicit Signal and Evidence Roles

Every newly collected daily candidate MUST identify whether it is a realtime `signal` or supporting
`evidence`; GitHub repository/search and Papers default to `evidence`, while direct or watchlist
WeChat articles, Hacker News and X default to `signal`. Evidence-only items MUST NOT independently
seed the daily Top list.

#### Scenario: Only evidence was collected

- **WHEN**the freshness window contains GitHub snapshots or Papers but no realtime signal
- **THEN**the daily result is `no_fresh_signals`
- **AND**evidence items are not used to fill the Top list

### Requirement: Verifiable Freshness

A Top signal MUST have a parseable source publication timestamp inside the configured maximum age;
`discovered_at` MAY describe when the system first saw an item but MUST NOT substitute for an unknown
publication time. Source timestamps SHALL normalize to timezone-aware UTC; legacy timezone-naive
WeChat timestamps SHALL be interpreted as Asia/Shanghai. The exact lower freshness boundary is
inclusive, while timestamps more than 5 minutes in the future are excluded as unverifiable clock skew.

#### Scenario: First observed item has unknown publication time

- **WHEN**an item is first observed today but has no parseable `published_at`
- **THEN**it is excluded from the verified fresh Top list
- **AND**the system does not label it as published today

#### Scenario: Timestamp is exactly on or outside the freshness boundary

- **WHEN**one signal is published exactly `freshness_hours` before evaluation, another is one second older and a third is more than 5 minutes in the future
- **THEN**only the exact-boundary signal passes the freshness gate
- **AND**evaluation uses the configured timezone-aware `now` rather than filesystem modification time

### Requirement: Deterministic Signal Ranking

Daily ranking SHALL prioritize 24-hour freshness band, configured watchlist membership, independent
corroboration, source-local engagement percentile and publication time, in that order. Engagement
percentile SHALL be calculated only among candidates from the same source in the current run (a
single candidate receives the neutral value `0.5`); raw engagement counts from different platforms
MUST NOT be directly compared. Remaining ties SHALL use normalized canonical URL and title so repeated
runs produce the same order.

#### Scenario: Watchlist signal competes with lifetime-popular evidence

- **WHEN**a fresh watchlist signal and a highly starred historical GitHub repository are present
- **THEN**the watchlist signal ranks in the daily Top list
- **AND**the repository may only appear as supporting evidence

### Requirement: Cross-Source Dedupe and Corroboration

Signals referring to the same normalized destination or exact normalized title SHALL be merged into
one Top item, while independent matching evidence SHALL increase its corroboration context. URL
normalization SHALL lowercase scheme/host, remove fragments and known tracking parameters, and
normalize trailing slash. Title normalization SHALL apply Unicode NFKC, lowercase text, remove
punctuation and collapse whitespace; fuzzy semantic matching is outside this deterministic layer.

#### Scenario: One event appears on multiple sources

- **WHEN**two fresh signals share a normalized destination URL or equivalent title
- **THEN**the daily briefing contains one Top entry
- **AND**the entry preserves all contributing source links and matched evidence
