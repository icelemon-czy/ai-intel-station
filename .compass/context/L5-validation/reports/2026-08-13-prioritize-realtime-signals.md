# 验证报告 — Prioritize Realtime Signals

> 日期: 2026-08-13
> Change: `prioritize-realtime-signals`
> Result: PASS

## Scope

把 daily intelligence 从 GitHub lifetime popularity / arXiv category-first 调整为
realtime signal-first：Hacker News、configured WeChat account 与 optional X 发起 candidate，
GitHub repository/search 与 Papers 只作 evidence。Daily output 增加 verified publication-time
gate、deterministic dedupe/ranking/confidence、最多 5 条 Top item，以及 honest coverage status。

## Contract Evidence

- `ResearchItem` 新增 backward-compatible `discovered_at`、`signal_role`、`discovery_method`，
  重复观测保留 first-seen，historical backfill 不捏造当前 discovery time。
- Realtime adapters 使用 bounded local fixture 验证 HN success/failure、X explicit
  `start_time/end_time` 与 credential boundary、WeChat index attribution/CAPTCHA/empty/malformed/
  missing-time failure。
- `briefing/signals.py` 只允许 verified fresh `signal` 发起 Top item；GitHub/Papers evidence-only。
  Ranking 使用 24h band、watchlist、independent corroboration、within-source engagement percentile、
  publication time 与 stable URL/title tie。
- Outcome 为 `ready|partial|no_fresh_signals|coverage_incomplete`；`failed|dry_run|legacy`
  不得伪装成 today's signal result。CLI marker、run log、Web payload 与 Web UI 均保留 status。
- Existing explicit digest/reading-list config 保持 legacy behavior；standalone `research collect`
  仍只有 GitHub/Papers/WeChat，HN/X 仅是 discovery selector。

## Automated Verification

### Python targeted / core

```text
tests/test_realtime_signals.py + briefing marker/log/Web targets
52 passed + 4 unittest subtests

core gate (not wechat; runner compatibility and npm wiring separated)
426 passed, 26 skipped, 2 deselected + 4 unittest subtests

python -m unittest tests.test_discovery_runner
15 passed

optional WeChat marker gate
16 passed, 7 deselected
```

Skipped tests are pre-existing environment-gated live/loopback cases, not product failure. Realtime
collector behavior was validated with local fixtures; no live response was packaged as regression evidence.

### Web

```text
node --test test/*.test.mjs
102 passed, 0 failed, 2 loopback skips

vite build
33 modules transformed; production build succeeded
```

The frontend regression renders real exported `StatusBlock` and `ResultReport` components and proves
that `no_fresh_signals` is visibly different from `coverage_incomplete` in both latest-status and
completed-job paths. `esbuild` is now an explicit dev dependency because Node tests import it directly.

### Config / operator smoke

- Personal ignored config uses signal mode, HN enabled, X disabled, and WeChat watchlist
  `{name: 架构师, wechat_id: JiaGouX}`.
- Network-free dry-run completed with 9 succeeded source/config actions and no failed action.
- No schedule was installed or changed.

## SDD Review

The same read-only `sdd-reviewer` performed plan and verify review.

1. Plan review initially blocked ambiguous empty coverage, missing CLI ownership, incomplete evidence-role
   migration, source success/failure scenarios, status compatibility, and deterministic boundary contracts.
   Delta Specs/tasks were repaired before implementation.
2. Verify round 1 found new marker parsing and X time-range gaps; both were fixed with regression tests.
3. Verify round 2 found the Web UI discarded structured briefing status; both UI branches and real SSR tests
   were repaired.
4. Final verify result: PASS; no remaining Spec, compatibility, security, implementation or anti-overfit blocker.

## Known Boundaries

- WeChat arbitrary-account discovery remains best-effort through a public index; CAPTCHA or incomplete
  metadata lowers coverage instead of being called a quiet day.
- X is disabled by default and requires an explicitly configured bearer-token environment variable.
- Fuzzy semantic dedupe is outside the deterministic layer; URL and exact normalized title matching are used.
- Live WeChat/X network e2e was not required for this fixture-driven product contract.

## Conclusion

Implementation, docs, main Specs, traceability and Web consumer now share one signal-first contract.
All mandatory local gates passed; environment-dependent loopback/live cases remain explicitly skipped.
