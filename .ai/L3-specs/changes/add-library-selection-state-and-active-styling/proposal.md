# add-library-selection-state-and-active-styling

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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户明确指出 Library 结果选中后缺少可感知的 active state，需要独立提案评估

## Why

当前 Library 结果列表点击后只会在右侧详情面板变化，左侧 result card 本身没有稳定、明确的选中态。用户需要同时盯住两块区域才能确认自己点中了哪一条，这对检索和比对资料尤其低效。

既然 Library 是 Web 中最典型的“列表 + 详情”交互，这种选中反馈不能作为纯视觉细节，而应被视为基础可用性需求。

## What Changes

- 为 Library 结果列表增加明确的 active state、hover state 和 focus state
- 支持选中项在视觉上明显高亮，例如深色背景 + 浅色文字
- 保证选中项与右侧详情面板同步，并在刷新结果后保持合理默认项
- 补充键盘导航和移动端触控反馈，避免只有鼠标点击场景可用

## Alternatives Considered

1. **只在右侧详情面板变化，不改左侧列表** — 实现最省事，但用户仍然不知道当前高亮的是谁
2. **把选中态作为 Library 的基础交互能力补齐（当前选择）** — 直接提升可辨识性和操作稳定性

## Capabilities Affected

### New Capabilities

- `research-web-library-interaction`: 定义列表项选中、焦点和详情联动的交互要求

### Modified Capabilities

- `research-web-workspace`: 强化 Library 列表的可见反馈与可用性

## Impact

- 影响范围：`web/src/App.jsx`、`web/src/styles.css`、可能新增前端交互测试
- 建议优先级：P0
- 建议顺序：2 / 10
- 依赖：`add-react-web-workspace-mvp`；可与信息架构改名并行

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只解决选中态和交互反馈，不包含采集工作台或 jobs 能力
