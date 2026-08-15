# 验证报告 — Add Daily Source Quotas

> 日期: 2026-08-14
> Change: `add-daily-source-quotas`
> Result: PASS

## Scope

Daily signal briefing 从 legacy News cap 扩展为 default 5 条 News（其中至少 2 条 deduped
WeChat）+ 1 条 GitHub + 1 条 arXiv。GitHub/Papers 保持 evidence role，只能进入 dedicated
lane；stale、timestamp-unknown 或 wrong-lane item 不得补 quota。Source failure、selective omission
与 quota shortfall 使用 honest `partial|coverage_incomplete` outcome。

## Contract Evidence

- `BriefingConfig` 支持 strict-integer `news_items`、`wechat_min_items`、`github_items`、
  `paper_items`，并保留 max-only legacy cap migration；explicit empty sources、field conflict、
  bounds/relation 与 positive-quota source viability 在 network 前聚合报错。
- `select_daily_briefing()` 保留 News selector，并新增 Paper/GitHub source-time gate 与独立 ranking。
  Exact duplicate ownership 为 `papers > github > news`；loser 选择 distinct replacement 或 shortfall。
- WeChat minimum 按 rendered deduped News entry 计数。Duplicate raw WeChat 与 mixed WeChat/HN group
  均由 public selector assertion 验证，不能按 raw candidate 虚假计数。
- Dedicated confidence boundary 为 source-only `low`、single non-watchlist `medium`、two-source 或
  WeChat watchlist `high`；why-now 暴露 lane、timestamp field、age band 与 corroboration reason。
- Runner item count、Markdown 三段、quota expected/actual/missing、dry-run composition 与 Agent Skill
  均使用 default 7-item contract。任意本次 attempted enabled source failure 都不能与 `ready` 共存。

## Automated Verification

```text
targeted quota/config/Skill suites: 83 passed
core gate (runner adapter + npm process wiring separated): 470 passed, 27 skipped,
  1 npm-process test deselected, 4 subtests passed
python -m unittest tests.test_discovery_runner: 15 passed
optional WeChat marker gate: 16 passed, 7 deselected
L3 structure/alignment gates: 11 passed
Web Node suite: 102 passed, 0 failed, 2 sandbox loopback skips
```

The environment did not expose `npm` on PATH, so the Python process-level npm wiring test was
deselected. The same installed Web suite was executed directly with the bundled Node runtime. The two
skips require loopback socket binding blocked by the sandbox and are retained as limitations, not successes.

## Operator Smoke

The ignored personal config was migrated without changing source targets or private values. Network-free
`research discover --dry-run` reported 9 planned succeeded actions, 0 failed, and:

```text
composition=5 News (WeChat minimum=2) + 1 GitHub + 1 arXiv
```

No live discovery or schedule action was added by this change.

## SDD Review

The read-only reviewer completed three plan rounds and three verify rounds. Verify repairs covered
explicit-empty source fallback, all-attempted failure scope, strict integer validation, independent
shortfall/dedupe/duplicate/confidence assertions, and GitHub/Paper source-time/ranking boundaries.
Final verdict: PASS with no remaining blocking finding.

## Known Boundaries

- WeChat public index remains best-effort. CAPTCHA、empty/malformed response、missing attribution/time
  are source failure and may leave the 2-item minimum short; they are not interpreted as a quiet day.
- X remains optional and disabled by default. Five News entries may come from HN/WeChat/X, but only
  WeChat has a default source-specific minimum.
- Fuzzy semantic dedupe remains outside the deterministic layer.

## Conclusion

Implementation、tests、Agent/docs、main Specs、L1/L2 与 traceability now share the same 5/2/1/1
composition and honest coverage contract. All mandatory local gates passed subject to the documented
sandbox-only Web limitations.
