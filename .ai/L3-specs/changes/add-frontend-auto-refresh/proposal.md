# Add Frontend Auto-Refresh

> **状态**: approved
> **创建**: 2026-06-02
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

## Status Machine（不要删）

```text
drafting ──→ implementing ──→ pending-review ──→ approved ──→ archived
   ↑              ↑  ↑              │
   │              │  └──────────────┘
   │              │   review 打回 (review-failed → implementing)
   │              │
   └──────────────┘
     spec 歧义回退（走 /fix-bug Step 3C）
```

| 状态 | 含义 | 由谁推进 |
|:-----|:-----|:---------|
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal）|
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿）|
| pending-review | review-failed | /review-tests（打回）|
| review-failed | implementing | /fix-bug（开始修）|
| pending-review | approved | /review-tests（通过）|
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-06-02 00:00` — [无] → [drafting] by /new-change | 原因: 创建前端 auto-refresh proposal，等待业务确认
- `2026-06-02 00:05` — [drafting] → [implementing] by /new-change | 原因: 业务确认推进（轮询 5s、顶栏 toggle、仅读路径 + collect sources、保留表单状态）

## Why

当前 Web 工作台每个 section 只在 mount 时拉一次数据，开发者运行 `collect` 后必须切换 tab 才能在 Library/Dashboard 看到新条目。本变更给三个读路径（Library / Briefing / Dashboard）以及 Collect 的 source 列表增加**轮询刷新**能力，并通过顶栏 toggle 让用户能一键关闭。

## What Changes

- 顶栏新增 `Auto-refresh` toggle，开关默认 `true`
- 当 toggle on 且 active section 是 Library/Briefing/Dashboard/Collect 时，每 5 秒重新拉取该 section 的数据 endpoint
- 轮询期间保留用户输入状态（Library 的 keyword/sources/page、Briefing 的 mode/title/form、Collect 的 activeSource）
- toggle off 时，行为退回到当前（mount 时拉一次）
- 切换 active section 时立即拉一次新数据（已有部分逻辑），并把新 section 加入轮询

## Alternatives Considered

1. **WebSocket / SSE** — 延迟 < 1s 但需后端 filewatcher 依赖。讨论后用户选择 polling（更简单、与 Vite HMR 解耦）
2. **每页独立 toggle** — 粒度更细但 UI 复杂。讨论后用户选择单 toggle
3. **仅 mount + tab 切换时拉，不轮询** — 最轻但 collect 后无反馈。讨论后用户选择 5s 轮询

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Web 工作台在前端为读路径 section 增加可关闭的 5s 轮询刷新

## Impact

- 前端：`web/src/App.jsx`（加 hook + toggle UI）、可能涉及 `web/src/styles.css`
- 后端：不变。`/api/library` / `/api/dashboard` / `/api/collect/sources` 已存在且幂等
- 测试：`tests/test_web_workspace.py` 增加轮询 hook 的契约测试（不引入 JSDOM，用纯 JS 模块导出 + 单元测试）
- 不涉及真实采集逻辑、输出格式、外部依赖

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不实现差分轮询（每次拉全量）；local-first 工作区数据量小可接受
- [ ] 不暴露轮询间隔为用户可配；5s 硬编码
- [ ] 不引入可见的"上次刷新于 X 秒前"时间戳（可后续加）
