# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 Topbar exposes an `Auto-refresh` toggle default-on
- [x] 1.2 Hook issues a fetch on a 5s interval when toggle is on and a section is active
- [x] 1.3 Hook stops the interval when toggle is turned off
- [x] 1.4 Hook does not mutate form state when a polling fetch returns
- [x] 1.5 Section switch triggers an immediate fetch and rejoins polling
- [x] 1.6 No new query parameters are added to the polled requests (backend contract preserved)

## 2. Frontend: polling hook (pure JS, testable without JSDOM)

- [x] 2.1 抽出一个 `useAutoRefresh({ section, enabled, intervalMs, fetcher, onData, onSectionChange })` hook 在 `web/src/autoRefresh.react.js`
- [x] 2.2 hook 暴露内部接口（`getCurrentTimerId` / `lastFetchSection`）供测试
- [x] 2.3 hook 在 `enabled === false` 时清理 interval
- [x] 2.4 hook 切换 section 时立即 fetcher.onSectionChange + 重启 interval
- [x] 2.5 暴露 `POLLING_INTERVAL_MS = 5000` 常量

## 3. Frontend: topbar toggle + App.jsx 集成

- [x] 3.1 App 组件顶栏加 `<input type="checkbox">` + 标签 `Auto-refresh (5s)`
- [x] 3.2 App 顶层 `useState(autoRefreshEnabled, true)`
- [x] 3.3 在 4 个 section（Dashboard / Library / Briefing / Collect）使用 `useAutoRefresh` 调它们各自的 fetcher
- [x] 3.4 fetcher 调用现有的 `requestJson` 不改契约
- [x] 3.5 保留所有 form state（不改 setForm / setKeyword / setActiveSource / setPage 等）
- [x] 3.6 加最小 CSS（toggle 样式）

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿（含 1.1-1.6）
- [x] 4.2 端到端：在另一 shell 运行 `uv run research collect papers cs.AI --max 3`，5s 内 Library 总数 +1

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
