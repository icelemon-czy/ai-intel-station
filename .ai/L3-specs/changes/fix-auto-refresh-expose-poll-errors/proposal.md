# Fix: Expose Auto-Refresh Polling Errors

> **状态**: approved
> **创建**: 2026-06-02
> **父变更** (parent-change): `add-frontend-auto-refresh`
> **嵌套深度** (depth): 1

## Why

`add-frontend-auto-refresh` 让 4 个 section 顶栏 toggle 启用时每 5 秒轮询对应 endpoint，但当 fetch 失败时 `createAutoRefreshController.runOnce` 内部 try-catch 静默吞掉错误。Review #1 (2026-06-02) 登记为 known gap：用户看不到 polling 是否在跑、是否失败、为什么失败。

本变更给 controller 增加 `onError` 回调，让 App.jsx 在 UI 显示一条非阻塞的 polling error 状态。

## What Changes

- `createAutoRefreshController` 增加可选 `opts.onError(section, error)` 回调
- `runOnce` 在 fetcher reject 时调用 `onError`（仍不打破 interval — 这是 spec 已约束的行为）
- 暴露一个新的 `getLastError()` 状态供 UI 读取
- App.jsx 增加一个轻量级 error banner：在 active section 的顶部展示最后错误 + "Dismiss" 按钮
- 文案约束：错误信息是 fetch 异常的 message（不泄露敏感信息）
- 不改变：interval 5s、不变 polling 行为、不改 backend contract

## Alternatives Considered

1. **完全静默**（当前）— UX 差，用户不知道 polling 是否健康
2. **改 polling 间隔为指数退避** — 复杂度高，spec 已固定 5s
3. **在 UI 顶栏加红点指示** — 信号弱，文案 + banner 更直接

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: Web 工作台 polling 行为在错误时 MUST 暴露给 UI

## Impact

- 前端：`web/src/autoRefresh.js`（加 onError 路径）、`web/src/autoRefresh.react.js`（转发 onError）、`web/src/App.jsx`（error banner）、`web/src/styles.css`
- 后端：无
- 测试：`web/test/autoRefresh.test.mjs` 加 2 个 Node 测试（error 触发 + getLastError 状态）；`tests/test_web_workspace.py` 加 1 个 App.jsx 契约测试

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不重试 / 不退避；连续失败时仍按 5s 节奏
- [ ] 不记录历史错误；只保留最后一次
- [ ] 不区分 4xx / 5xx；用户看到的就是 fetch 异常的 message
