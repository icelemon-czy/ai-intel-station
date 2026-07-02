# Fix: Add JSDOM React Render Tests for Auto-Refresh

> **状态**: pending-review
> **创建**: 2026-06-02
> **父变更** (parent-change): `add-frontend-auto-refresh`
> **嵌套深度** (depth): 1

## Status Transfer Log

- `2026-06-02 00:00` — [无] → [drafting] by /fix-bug | 原因: 父变更 `add-frontend-auto-refresh` review #1 登记 React 渲染层覆盖为 known gap
- `2026-06-02 13:00` — [drafting] → [implementing] by /continue-change | 原因: spec+test+code 实施中
- `2026-06-02 18:00` — [implementing] → [pending-review] by /continue-change | 原因: 6 个 Node SSR tests + 1 个 npm subprocess test 全绿
- `2026-06-07 12:00` — [pending-review] → [review-failed] by /review-tests | 原因: `test_npm_test_in_web_runs_node_test_suite` 硬编码 `pass 24/25/26`，实际 `pass 46` 导致红灯；反模式 #2 断言过严
- `2026-06-07 12:30` — [review-failed] → [implementing] by /fix-bug | 原因: 改写 assertion 为解析 `ℹ pass N` / `ℹ fail N` / `ℹ skipped N` 三行，断言 `pass > 0` + `fail == 0` + `skipped == 0`，匹配 Spec Scenario 6 "report pass/fail counts"
- `2026-06-07 12:30` — [implementing] → [pending-review] by /fix-bug | 原因: `tests/test_web_workspace.py::test_npm_test_in_web_runs_node_test_suite` 红灯转绿，`tests/test_web_workspace.py` 全量 95 passed / 1 skipped

## Why

`add-frontend-auto-refresh` 的所有契约测试都是源文本子串匹配 + 纯 Node 测 `createAutoRefreshController`。这不能证明：(a) React `useEffect` 真的让 `setInterval` 跑起来、(b) `useState` 真的更新 banner 渲染、(c) section 切换时 useEffect 的依赖清理正确执行。

review #1 (2026-06-02) 登记为 known gap。

## What Changes

- 新增 `web/test/autoRefresh.react.test.mjs` — 用 `react-dom/server` (JSDOM-free) 的 `renderToString` 给 `useAutoRefresh` 在多种 props 下做 SSR 渲染测试，验证：
  - `lastError` 为 null 时不渲染 banner
  - `lastError` 不为 null 时渲染 banner 文案（取自 error.message）
  - 切换 `section` prop 时 hook 重置 lastError
- 新增 `tests/test_web_workspace.py` 子测试 — 通过 `subprocess` 调用 `npm test --prefix web`，确认 Node test 套件（含新增）已纳入 npm test
- 不引入 JSDOM 依赖（避免重型改动）；用 React 18 已带的 `react-dom/server`
- 不改变后端；不改变生产代码

## Alternatives Considered

1. **引入 vitest + JSDOM** — 改测试栈，dev 依赖 + 10MB。复杂度高
2. **用 `@testing-library/react` + jsdom** — 同样重型
3. **SSR 渲染测试（当前选择）** — 用 React 自带 `renderToString` 验证渲染结果，零新依赖，覆盖 80% 的"组件收到 props 渲染正确"语义

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: 自动化测试覆盖 React 真实渲染层

## Impact

- 前端：`web/test/autoRefresh.react.test.mjs` (新)
- 测试：`tests/test_web_workspace.py` 加 1 个 subprocess 测试
- 工具：`web/package.json` 加 `test` 脚本（`node --test test/`）
- 不涉及业务代码、不涉及 build、不涉及后端

## Review Feedback

- [x] 2026-06-07 [reviewer]: `test_npm_test_in_web_runs_node_test_suite` 硬编码 `pass 24/25/26` 过窄，实际 `pass 46` → 红灯。Spec Scenario 6 只要求"all run via `node --test` and report pass/fail counts"，未指定具体数字 → 改写为解析 `ℹ pass N` / `ℹ fail N` / `ℹ skipped N` 三行，断言 `pass > 0 && fail == 0 && skipped == 0` → 状态: resolved by /fix-bug session 2026-06-07

## Known Gaps

- [ ] 不覆盖 timer 真实 fire 行为（`renderToString` 同步渲染）
- [ ] 不覆盖 unmount 时 cleanup（SSR 没 lifecycle）
- [ ] 仍依赖源文本子串测试作为 React 集成的 fallback
