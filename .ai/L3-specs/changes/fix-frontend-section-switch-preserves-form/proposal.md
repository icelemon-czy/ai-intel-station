# Fix: Preserve Library Form State Across Section Switches

> **状态**: pending-review
> **创建**: 2026-06-03
> **父变更** (parent-change): `add-frontend-auto-refresh`
> **嵌套深度** (depth): 1

## Why

`App.jsx` 当前结构是 `{activeSection === "library" ? <LibrarySection /> : null}` —— 切换到 Dashboard 时 LibrarySection unmount，切回时**重新挂载**。LibrarySection 内部用 `useState({ keyword: "agent", sources: [...], ... })` 初始化 form，**任何用户输入都会在 unmount 时丢失**。

review #1 (2026-06-02) 登记为 known gap：Node 测试只验证 controller 不改 form，**没验证 React unmount/remount 时 form 是否保留**。spec 4 (`add-frontend-auto-refresh/specs/.../spec.md` 的 "Polling preserves user inputs") 已被此 bug 违反。

## What Changes

- `App.jsx` 把 4 个 section 的 form 状态**提升**到顶层 App 组件（`useState`）—— 这样即使子 section unmount，状态在父组件仍存活
- `LibrarySection` 接收 `form` / `setForm` / `page` / `setPage` 作为 props
- `BriefingSection` / `CollectSection` 同理（虽然它们 form 较简单，仍受益于统一模式）
- 不改变 useAutoRefresh 行为；polling 期间 form 仍保留
- 不改变后端

## Alternatives Considered

1. **Persist form to localStorage** — 跨会话保留，但 spec 不要
2. **Keep section mounted but hide it** — `display: none` 而非 unmount，状态保留但有副作用（后台仍在轮询）
3. **Lift state to App 顶层（当前选择）** — 简单、明确、与 spec "Polling preserves user inputs" 一致

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: Library form 状态 MUST 在 section 切换时保留

## Impact

- 前端：`web/src/App.jsx` 顶层加 4 个 form 状态，4 个 section 改用 props
- 不涉及后端 / build / 依赖

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不实现 localStorage 跨会话保留
- [ ] 不做 SSR hydration 兼容（用户刷新页面 form 重置 — 同当前行为）
- [ ] 不修改 spec "Topbar exposes Auto-refresh toggle" 等等其它
