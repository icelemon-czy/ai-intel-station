# Fix: Add JSDOM React Render Tests for Auto-Refresh

> **状态**: pending-review
> **创建**: 2026-06-02
> **父变更** (parent-change): `add-frontend-auto-refresh`
> **嵌套深度** (depth): 1

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

- [ ] 无

## Known Gaps

- [ ] 不覆盖 timer 真实 fire 行为（`renderToString` 同步渲染）
- [ ] 不覆盖 unmount 时 cleanup（SSR 没 lifecycle）
- [ ] 仍依赖源文本子串测试作为 React 集成的 fallback
