# [变更名称]

> **状态**: drafting / implementing / pending-review / review-failed / approved / archived
> **创建**: YYYY-MM-DD
> **父变更** (parent-change): 无 / `<上游变更名>`
> **嵌套深度** (depth): 0  <!-- 不得 ≥ 2，防止 /fix-bug 递归 -->

## Status Machine（不要删）

```
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
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项（技术问题或未解决的产品语义），记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /develop |
| drafting | implementing | /develop（必要业务决策完成 + plan review）|
| implementing | pending-review | /develop（相关测试全绿）|
| pending-review | review-failed | /develop（SDD review BLOCKED）|
| review-failed | implementing | /develop 或 /fix-bug（开始修复或落实已确认决策）|
| pending-review | approved | /develop（SDD review PASS）|
| approved | archived | /develop（自动合并并验证）|

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

<!-- 每次状态改动追加一行，不要改历史行 -->

- `YYYY-MM-DD HH:MM` — [从] → [到] by [skill 或 human] | 原因: [简短记录]

## Why

<!-- 1-2 句话说明问题或机会。为什么要做？为什么是现在？ -->

[填写]

## What Changes

<!-- 具体变更列表。标注破坏性变更为 **BREAKING** -->

- [填写]

## Alternatives Considered

<!-- 考虑过哪些备选方案？为什么选当前方案？ -->

1. **[方案 A]** — [优缺点]
2. **[方案 B（当前选择）]** — [为什么选这个]

## Capabilities Affected

<!-- 哪些能力域的 spec 会变？Agent 根据这里创建 delta spec -->

### New Capabilities
<!-- 新增的能力域，每个会创建新的 specs/<name>/spec.md -->

- `[capability-name]`: [简述]

### Modified Capabilities
<!-- 已有能力域的需求变更，每个需要 delta spec -->

- `[existing-capability]`: [什么需求在变]

## Impact

<!-- 影响范围：涉及哪些代码、API、依赖 -->

[填写]

## Review Feedback

<!-- 每次内部 SDD review 打回时追加一条，由 Main Agent 或 /fix-bug 解决后标记 resolved -->

- [ ] YYYY-MM-DD [reviewer]: [问题描述 / 反模式编号 / 文件:行] → 状态: open / resolved by [commit]

## Known Gaps

<!-- Review 认为"非阻塞"的缺口，允许归档但登记在案 -->

- [ ] [描述] — 计划在 [哪个后续变更] 补齐
