# upgrade-dashboard-from-overview-to-action-center

> **状态**: pending-review
> **创建**: 2026-05-27
> **父变更** (parent-change): add-react-web-workspace-mvp
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 当前 Dashboard 只做静态总览，用户要求把它推进成真正的行动中心，需要独立提案

## Why

现在的 Dashboard 更像一个展示面板：只告诉用户本地有多少资料、缺哪些 source、最近有哪些 briefing。它能看，但不能推动任何下一步，也不能解释数据是否过期、是否建议刷新、最近哪些任务失败。

一旦 Web 承担整项目的主交互层，Dashboard 就不该只是统计页，而应成为“下一步干什么”的行动中心。

## What Changes

- 为 Dashboard 增加 freshness、新旧程度、最近任务、失败摘要和下一步 CTA
- 把“最近 briefing”扩展成“最近产物 + 最近操作 + 推荐动作”的组合视图
- 在 Dashboard 上直接暴露去采集、去资料库、去生成简报等入口
- 明确区分“数据缺失”“数据过旧”“依赖未就绪”三类状态

## Alternatives Considered

1. **保持 Dashboard 只做总览，把行动入口放到别的页面** — 结构更简单，但首页不会真正推动工作流
2. **把 Dashboard 升级为行动中心（当前选择）** — 能让首页承担“看现状 + 做下一步”的职责，但依赖更多后续能力落地

## Capabilities Affected

### New Capabilities

- `research-web-dashboard-operations`: 定义 Dashboard 的任务摘要、freshness 和 CTA 行为

### Modified Capabilities

- `research-web-workspace`: 扩展首页从静态总览到可操作入口

## Impact

- 影响范围：`workspace_web/service.py`、Dashboard API、前端首页布局、文案
- 建议优先级：P1
- 建议顺序：8 / 10
- 依赖：强依赖 `add-local-job-runner-and-job-history`，推荐在 collect shell 和 diagnostics 之后实施

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 若 jobs、schedule 和 diagnostics 尚未落地，本提案只能先做部分动作入口，不能一次性补齐全部行动能力
