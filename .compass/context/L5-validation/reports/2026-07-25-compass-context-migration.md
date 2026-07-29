# 验证报告 — 2026-07-25 Compass Context Migration

## Scope

- 将 old `.ai` facts 合并到 `.compass/context`
- 重建 L3 main Specs、change-management 与 templates
- 将 daily discovery runtime default 从 agent context 迁到 `.state/discovery/`
- 重建 10 个 capability 的 L5 traceability

## Structure

- Capability: 10
- Requirement: 53（daily-discovery delta merge 后）
- Scenario: 59（daily-discovery delta merge 后）
- 每个 Requirement 至少一个 Scenario
- business Spec 无 template placeholder 或重复 Requirement；仅 daily-discovery compatibility Scenario 保留 legacy `.ai` path

## Commands and results

| Command / surface | Result |
|:------------------|:-------|
| business Spec structure + fresh Compass template comparison | PASS |
| `python -m pytest` broad Python surface，排除 runner duplicate、npm wiring 与 3 个 socket cases | 392 passed, 24 skipped, 4 deselected |
| `python -m unittest tests.test_discovery_runner` | 14 passed |
| migration + config + schedule + discovery Web | 28 passed |
| Node Web suite in sandbox | 100 passed, 2 socket-dependent skipped |
| 3 fixed-port server tests outside sandbox | 3 passed |
| production Web build | PASS，checked-in bundle 已更新 |
| Node Web suite outside sandbox | 100 passed, 2 failed, 0 skipped |

## Verified migration behavior

- 未配置 `log_dir` 时使用 repository-local `.state/discovery/`
- run、`--status` 与 `--log-list` 使用同一 configured directory
- arbitrary explicit `log_dir` 继续有效
- 旧模板显式值 `.ai/L4-session/discovery/` 继续作为 override
- migration 不移动、改写或额外删除旧 sentinel；existing retention 保持
- fresh cron 先创建 `.state/discovery/` 再执行 redirect 与 discovery
- Web run 使用 payload config 解析出的 `log_dir`
- embedded example、checked-in example、cron、Web source、built bundle 与 ignore boundary 同步

## Findings

### Partial — legacy datetime breaks one real Library Web round-trip

`web/test/fullstack.real_e2e.test.mjs` 使用 repository output 时遇到
`2026-04-02 08:31`，strict datetime parsing 使 API request 返回 error。
valid fixture 的 unit/direct tests 通过，但 existing-data compatibility 未闭合。

对应 evidence:

- `.compass/context/L5-validation/traceability/library.md`
- `.compass/context/L5-validation/traceability/web-workspace.md`
- `.compass/context/L5-validation/test-specs/library.md`

### Test defect — HTTP contract probe ignores method

`web/test/fullstack.contract.test.mjs` 从 frontend bundle 提取
`/api/briefing/preview` 后统一用 GET probe；该 endpoint 是 POST，因此返回 404。
这条 failure 不能作为 backend 缺 endpoint 的 evidence，后续应让 contract test 同时建模 method。

### Cleanup completed

user 明确授权后，已删除 `.compass/context/L3-specs/changes|archive` 中被 main Specs
吸收的 16 个 old active change 与 23 个 old archive change。删除前逐目录审计确认它们
均存在 `.ai` counterpart；normalize `.compass/context` → `.ai` 后共比对 39 个目录、
142 个文件，`mismatches=0`。

删除后 `.ai` 仍完整保留 240 个文件；active changes 仅保留 `_change-template`，
archive 仅保留新创建且已验证的 `migrate-discovery-state-out-of-ai`。

## Conclusion

L3 main Specs、runtime migration 与 L5 evidence 已通过相关验证。当前已知 product gap
是 legacy datetime compatibility；当前已知 test gap 是 method-insensitive HTTP contract probe。
两者均与 discovery state migration 无直接回归关系，但不能记作 full Web verification。

## Release cleanup addendum — 2026-07-30

legacy datetime 与 HTTP contract probe 后续均已修复并归档。user 完成 review 且明确授权删除后，
release cleanup 删除 240-file `.ai` snapshot、legacy Codex Skills 与 retired
GitHub/Claude Workflow mirrors。历史原文仍由 deletion 前 Git commit 保存；active source of
truth 只保留 `.compass/context` 与 `.agents/skills`，platform 目录仅保留 daily-discovery
thin adapter。

本项目的 release policy 明确把 merged Spec 与 project Workflow 作为 versioned
project artifacts，因此不采用 generic installer 的 local-only Git exclude 默认值。否则
release 会删除 tracked `.ai` truth 却不交付 replacement。installation staging 仍按 0.4.0
contract 清理为只剩 `.compass/context/`；installed `build-context` 已修正为不依赖清理后的
`INSTALL.md`。
