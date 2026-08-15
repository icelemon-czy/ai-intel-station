# Implementation Tasks

## 1. Tests

- [x] 1.1 Default config/example expose a viable enabled 5-News/2-WeChat-min/1-GitHub/1-Paper composition; legacy `max_items: 5` remains a cap where one fresh item can be ready; mixing legacy/new fields fails before network.
- [x] 1.2 Selector produces exactly 5 news (at least 2 WeChat) + 1 GitHub + 1 Paper when sufficient fresh candidates exist, without cross-lane substitution.
- [x] 1.3 When fewer than 2 fresh WeChat items exist, other news may fill the total news lane but renderer reports the WeChat minimum shortfall and returns partial.
- [x] 1.4 WeChat minimum counts deduped News entries containing WeChat; duplicate raw WeChat and mixed WeChat/HN groups cannot falsely satisfy two slots.
- [x] 1.5 Papers use `published_at`; GitHub uses `updated_at` fallback `published_at`; discovered-at-only, stale and future-skew evidence are excluded.
- [x] 1.6 GitHub lane prioritizes newly created fresh repositories over old updated repositories regardless of lifetime stars; Paper and news ranks remain deterministic.
- [x] 1.7 Exact normalized URL/title cross-lane duplicates use papers>github>news ownership, render once, retain corroboration, select a distinct replacement or create the losing lane shortfall.
- [x] 1.8 Dedicated source-only item is low confidence; one non-watchlist signal is medium; two independent signals or WeChat watchlist+evidence is high, with lane/timestamp reasons.
- [x] 1.9 Renderer groups arXiv/GitHub/News, exposes expected/actual/missing quota coverage and returns ready only when quotas, WeChat minimum and source coverage are complete.
- [x] 1.10 Status matrix covers positive quota source absent/disabled/no-target (config error), selective omission of all News providers or dedicated/WeChat source, enabled empty success, GitHub/Paper/WeChat failure, nonempty shortfall, complete empty and failed empty.
- [x] 1.11 Quota validation covers integer bounds, `wechat_min_items<=news_items`, total<=20, legacy/new conflicts, source membership and digest/reading-list compatibility.
- [x] 1.12 Runner passes quotas, reports total item count, and dry-run describes the 5 news (2 WeChat minimum) + 1 + 1 composition.
- [x] 1.13 Agent Skill accepts up to 7 grouped items and reports lane/WeChat shortfalls plus source coverage.

## 2. Config and Selection

- [x] 2.1 Add validated lane quotas and deterministic legacy `max_items` migration to BriefingConfig.
- [x] 2.2 Add dedicated GitHub/Paper freshness and ranking selectors while preserving the news selector.
- [x] 2.3 Compose three lanes without changing stored ResearchItem roles.

## 3. Briefing and Runtime

- [x] 3.1 Render grouped Markdown and quota coverage with honest status semantics.
- [x] 3.2 Wire lane quotas through discovery runner, artifact count and dry-run output.
- [x] 3.3 Update example and ignored personal config, then validate network-free dry-run.

## 4. Agent and Docs

- [x] 4.1 Update daily-discovery Skill, README and daily discovery docs to the default 7-item composition.

## 5. Verification and Context

- [x] 5.1 Run targeted, core, runner, optional WeChat and applicable Web/structure gates.
- [x] 5.2 Complete SDD verify review and repair all blocking findings.
- [x] 5.3 Sync L1/L2/L5, merge delta Specs, validate structure and archive the change.
- [x] 5.4 Update L2 global rule so evidence cannot seed News but may occupy its dedicated lane.
