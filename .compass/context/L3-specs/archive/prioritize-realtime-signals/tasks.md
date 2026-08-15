# Implementation Tasks

## 1. Tests

- [x] 1.1 Realtime source config accepts Hacker News, X and WeChat accounts while rejecting invalid feed, credential-env and watchlist shapes.
- [x] 1.2 Hacker News fixture collection preserves publication/discussion/engagement metadata; malformed, oversized and unavailable fixture responses fail explicitly without live network.
- [x] 1.3 X success fixture writes bounded recent-search signals; missing-token behavior makes no request, reports failure and does not block another source.
- [x] 1.4 WeChat public-index fixture discovers account articles; CAPTCHA, empty, malformed and missing-publication-time fixtures produce explicit incomplete coverage.
- [x] 1.5 Newly collected signal/evidence sidecars preserve role, first discovered time and discovery method across repeated observation; legacy/backfilled sidecars stay compatible without invented observation time.
- [x] 1.6 GitHub search uses recency ordering, preserves created/updated metadata and returns a real output Path.
- [x] 1.7 Daily selector covers timezone, inclusive age boundary and future-skew behavior; it excludes stale, timestamp-unknown and evidence-only seeds, including GitHub repo/search and Papers.
- [x] 1.8 Daily selector applies exact URL/title normalization, attaches corroborating evidence, normalizes engagement within each source and produces deterministic ties.
- [x] 1.9 Daily signal Markdown renders no more than 5 entries; why-now enumerates actual ranking reasons and confidence changes from low/medium to high only under the specified watchlist/corroboration/evidence rules.
- [x] 1.10 Complete empty run writes `no_fresh_signals`; empty partial-coverage run writes `coverage_incomplete`; partial run with items preserves results and failed coverage.
- [x] 1.11 `research discover --source` and help include Hacker News/X while standalone collect surface and credential-free core startup remain unchanged.
- [x] 1.12 Agent Skill accepts today's real ready/partial/no_fresh_signals/coverage_incomplete contract and rejects dry-run, failed, stale or legacy empty artifacts.
- [x] 1.13 Existing explicit digest/reading-list config remains compatible as legacy mode while initialized config defaults to bounded signal mode.

## 2. Unified Signal Model

- [x] 2.1 Extend ResearchItem with backward-compatible observation and source-role fields.
- [x] 2.2 Add builders and persistence for Hacker News, X, direct/indexed WeChat signals and GitHub/Papers evidence.
- [x] 2.3 Preserve old sidecar/backfill behavior, including first observation time, and update local query date handling where needed.

## 3. Realtime Collectors

- [x] 3.1 Implement bounded Hacker News public-feed collection and local archive output.
- [x] 3.2 Implement optional X recent-search collection using an explicitly configured token environment variable.
- [x] 3.3 Implement bounded WeChat account public-index discovery with CAPTCHA/access-block detection.
- [x] 3.4 Change GitHub search to recency metadata/order and return its artifact Path.

## 4. Discovery Runtime and Config

- [x] 4.1 Extend validated config, defaults, source selection and run reports for Hacker News/X/WeChat watchlists.
- [x] 4.2 Preserve source failure isolation and pass source coverage into briefing generation.
- [x] 4.3 Add the defined status enum to Markdown, artifact serialization, run log and read-only status; preserve legacy log parsing without treating it as a signal result.

## 5. Daily Signal Briefing

- [x] 5.1 Implement pure freshness gate, role filter, deterministic dedupe/corroboration and ranking.
- [x] 5.2 Render signal-first Markdown and explicit `no_fresh_signals` outcome.
- [x] 5.3 Keep generic digest/reading-list behavior backward compatible outside daily signal mode.

## 6. Agent and Personal Preferences

- [x] 6.1 Update daily-discovery Skill to consume the new status/coverage contract.
- [x] 6.2 Update the user's ignored discovery config to use signal mode, HN and the confirmed `架构师` watchlist; validate with dry-run.

## 7. Verification and Context

- [x] 7.1 Run targeted tests, core release gates and optional WeChat tests applicable to the changed paths.
- [x] 7.2 Complete SDD verify review and repair all blocking findings.
- [x] 7.3 Sync README/L1/L2/L5, merge delta Specs, validate structure and archive the change.
