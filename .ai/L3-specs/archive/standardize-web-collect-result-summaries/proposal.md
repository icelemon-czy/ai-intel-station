# standardize-web-collect-result-summaries

> **状态**: approved
> **创建**: 2026-05-27
> **父变更** (parent-change): align-web-collect-with-local-output-truth
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

- `2026-05-27 00:18` — `—` → `drafting` by `/new-change` | 原因: Web collect 已经有 UI，但当前各 source 返回值形状不一致，导致前端只能展示原始 JSON，需要单独收口结果契约

## Why

现在 GitHub / papers / WeChat 的 Web collect 返回结构彼此不一致，有的是 `None`，有的是原始字符串，有的是抓取对象，前端只能退化成原始 JSON dump。这样不仅用户难以理解成功与否，也让后续 jobs、历史页和 Dashboard 复用结果变得困难。

如果要让 collect 结果成为稳定的前端表面，就需要一个跨 source 的统一结果摘要契约，而不是每个 source 暴露自己内部返回值。

## What Changes

- 为 Web collect 定义统一的结果摘要结构，例如 `status`、`message`、`saved_paths`、`item_count`、`warnings`、`errors`
- 区分 success / partial / error 等状态，避免前端只能根据原始 payload 猜测结果
- 将 source-specific 细节放入可选扩展字段，而不是直接把内部原始对象暴露给 UI
- 让 Collect Workspace 能以统一卡片或摘要视图展示结果，而不是依赖 raw JSON

## Alternatives Considered

1. **继续让前端直接展示原始返回值** — 实现最少，但结果不可读，也无法稳定支撑 jobs/history 等后续能力
2. **定义统一结果摘要契约（当前选择）** — 增加一层协议设计，但能把 collect 输出变成稳定的 UI 和后续能力输入

## Capabilities Affected

### New Capabilities

- `research-web-collect-results`: 定义跨 source 的 collect 结果摘要契约和状态语义

### Modified Capabilities

- `research-web-collection`: Collect Workspace 从“能提交”扩展为“能稳定展示结果摘要”
- `research-web-wechat-collection`: WeChat 的成功 / 部分成功结果需要映射到统一契约
- `research-web-github-papers-collection`: GitHub / papers 的 repo/search/category 结果需要映射到统一契约

## Impact

- 影响范围：`workspace_web/service.py`、`workspace_web/server.py`、`web/src/App.jsx`、collect 相关测试
- 建议优先级：P1
- 建议顺序：2 / 4
- 依赖：强依赖 `align-web-collect-with-local-output-truth`

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不负责“采集后其他页面是否自动刷新”，只定义 Collect Workspace 应该拿到什么结果结构
