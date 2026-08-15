# Signal Discovery 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/signal-discovery/spec.md`
> 验证日期: 2026-08-15

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Realtime Signal Sources | HN success + malformed/unavailable | `collect/hackernews.py`, `research/discovery/runner.py` | `tests/test_realtime_signals.py` fixture success/failure/bound tests | ✅ verified |
| Realtime Signal Sources | X success + missing credential + explicit time range | `collect/x.py`, `research/discovery/config.py`, `runner.py` | `tests/test_realtime_signals.py` request/credential/fault-isolation tests | ✅ verified |
| GitHub Destination Cap in News | cap/replacement/shortfall, exact host boundary, cross-lane duplicate, mixed dual-cap, cap-zero outcome and exact exclusions | `briefing/signals.py::select_daily_briefing`, `DailyBriefingSelection` | `tests/test_realtime_signals.py` ranked pool, production YAML, host table, dual-cap and cap-zero assertions | ✅ verified |
| Explicit Signal and Evidence Roles | Dedicated-only evidence + papers>github>news ownership/replacement | `briefing/signals.py::select_daily_briefing` | `tests/test_realtime_signals.py` replacement/no-replacement/corroboration assertions | ✅ verified |
| Explicit Signal and Evidence Roles | Deduped optional WeChat and GitHub-destination maximum, replacement, cap shortfall and legacy minimum | `briefing/signals.py::DailyBriefingSelection`, `select_daily_briefing` | `tests/test_realtime_signals.py` cap/replacement + duplicate/mixed-group + positive minimum assertions | ✅ verified |
| Verifiable Freshness | News/Paper published, GitHub updated fallback published, unknown/stale/future boundary | `briefing/signals.py::select_daily_signals`, `select_daily_briefing` | `tests/test_realtime_signals.py` timezone/boundary + dedicated source-time assertions | ✅ verified |
| Deterministic Signal Ranking | News deterministic rank + GitHub created-first + Paper latest publication | `briefing/signals.py` | `tests/test_realtime_signals.py` created-vs-updated and public source-time/ranking tests | ✅ verified |
| Deterministic Signal Ranking | Dedicated low/medium/high confidence reasons | `briefing/signals.py::_dedicated_entry` via public selector | `tests/test_realtime_signals.py` independent three-boundary assertions | ✅ verified |
| Cross-Source Dedupe and Corroboration | Normalized URL/title merge with evidence | `briefing/signals.py` | `tests/test_realtime_signals.py` dedupe/corroboration tests | ✅ verified |

## Reverse traceability

未发现 signal collector、role/freshness gate、ranking 或 dedupe behavior 缺少 main Spec。
Fuzzy semantic matching 与 arbitrary private social feeds 明确不在本次 deterministic scope。
