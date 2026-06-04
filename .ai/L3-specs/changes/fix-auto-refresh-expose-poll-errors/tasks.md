# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射。

- [x] 1.1 fetcher rejection fires onError (Node test)
- [x] 1.2 getLastError returns the most recent error per section (Node test)
- [x] 1.3 successful fetch clears last error (Node test)
- [x] 1.4 dismissError clears the last error (Node test)
- [x] 1.5 App.jsx renders an error banner in the active section when getLastError is non-null
- [x] 1.6 App.jsx error banner is non-blocking (does not wrap form / button)

## 2. Backend (controller factory)

- [x] 2.1 `createAutoRefreshController` 增加 `opts.onError(section, error)` 回调
- [x] 2.2 `runOnce` 在 fetcher reject 时调用 onError + 存 lastError[section]
- [x] 2.3 暴露 `getLastError(section)` + `dismissError(section)`
- [x] 2.4 fetcher resolve 时清掉 lastError[section]
- [x] 2.5 保持"polling 失败不打破 interval"行为

## 3. Backend (React hook)

- [x] 3.1 `useAutoRefresh` 接受 `onError` 并把 lastError 存到 useState
- [x] 3.2 hook 返回 `lastError` 让 App.jsx 渲染 banner

## 4. Frontend (App.jsx)

- [x] 4.1 App 顶层加 `lastError` 状态 + `setLastError`
- [x] 4.2 4 个 section 的 fetcher.onError 把错误传给顶层
- [x] 4.3 渲染 `<div className="poll-error-banner">` 含 message + Dismiss 按钮
- [x] 4.4 加 CSS 样式

## 5. Wire it up

- [x] 5.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 5.2 跑 `web/test/autoRefresh.test.mjs` 全绿
- [x] 5.3 端到端：手动 kill 后端 / 改 endpoint 返回 500，UI 出现 banner
