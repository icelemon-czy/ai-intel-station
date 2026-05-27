# refresh-web-workspace-after-collect-run

> **状态**: drafting
> **创建**: 2026-05-27
> **父变更** (parent-change): standardize-web-collect-result-summaries
> **嵌套深度** (depth): 0  <!-- 不得 ≥ 2，防止 /fix-bug 递归 -->

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
| :----- | :----- | :--------- |
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
| :--- | :--- | :------------ |
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal） |
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿） |
| pending-review | review-failed | /review-tests（打回） |
| review-failed | implementing | /fix-bug（开始修） |
| pending-review | approved | /review-tests（通过） |
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-05-27 00:18` — `—` → `drafting` by `/new-change` | 原因: Web collect 已可提交，但 Dashboard / Library / Briefing 不会随采集结果联动刷新，需要独立提案补齐工作台闭环

## Why

即便 Web collect 成功，当前工作台的其他页面也不会自然反映新结果。用户往往还要手动刷新页面或重新搜索，才能看到刚刚抓进来的资料，这会让“采集成功”与“资料已进入工作台”之间出现明显断层。

如果 Web 要成为真正的一体化 workspace，collect 之后必须有明确的后续联动，而不是把用户丢回手工刷新。

## What Changes

- 在 collect 成功后刷新或失效 Dashboard、Library 和相关局部状态
- 为用户提供“去资料库查看”“查看新增归档”之类的下一步 CTA，而不是停留在结果摘要
- 处理 partial-success、无新增结果和失败场景下的页面反馈，避免误导用户以为资料库已更新
- 明确前端刷新策略是局部重取还是全页状态失效，保证交互连贯而不是静态页面跳转

## Alternatives Considered

1. **保持当前模式，只在 collect 页显示成功消息** — 成本最低，但工作台其余页面会长期滞后于真实归档状态
2. **让 collect 成功后驱动 workspace 联动刷新（当前选择）** — 增加一点状态管理复杂度，但能建立“采完就能用”的闭环体验

## Capabilities Affected

### New Capabilities

- `research-web-post-collect-refresh`: 定义 collect 完成后 Dashboard / Library / Briefing 的联动刷新与导航行为

### Modified Capabilities

- `research-web-collection`: collect 结果不再停留在当前页，而是驱动后续工作流
- `research-web-workspace`: 页面间状态需要承认 collect 引起的 archive 变化
- `research-query`: Web 侧需要在 collect 后重新消费最新 sidecar / archive 结果

## Impact

- 影响范围：`web/src/App.jsx` 状态管理、`workspace_web/service.py` 查询刷新方式、Collect / Dashboard / Library 交互
- 建议优先级：P1
- 建议顺序：3 / 4
- 依赖：`align-web-collect-with-local-output-truth`、`standardize-web-collect-result-summaries`

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不等同于 jobs history；即使联动刷新做完，也不自动获得 queued / running / failed 的时间线能力
