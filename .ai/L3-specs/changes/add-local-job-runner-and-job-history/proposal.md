# add-local-job-runner-and-job-history

> **状态**: pending-review
> **创建**: 2026-05-27
> **父变更** (parent-change): add-collect-workspace-shell
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户要求补“即时采集 / 定时采集”的能力，而这一切都先依赖可观测的本地 jobs 体系

## Why

没有 jobs 体系，Collect Workspace 只能是“填表后点一下按钮”，用户看不到 queued、running、success、partial、failed，也不知道执行到哪、失败在哪、能不能重试。同样，briefing 和 backfill 也无法进入统一的任务视角。

如果 Web 真的要承接 collect 和后续 schedule，那么 jobs 不是附属功能，而是整条执行链路的地基。

## What Changes

- 引入本地 jobs 模型和任务历史页
- 为 collect、briefing、backfill 提供统一的任务状态、日志、结果摘要和重试入口
- 区分 queued、running、success、partial、failed 等状态
- 让 Collect Workspace 和 Dashboard 都能消费 jobs 结果，而不是各自维护一套状态

## Alternatives Considered

1. **先不建 jobs，表单直接同步执行** — 实现更快，但后续 schedule、日志和失败重试都无法稳定扩展
2. **先建本地 jobs 与历史视图（当前选择）** — 增加一点基础设施成本，但能把 collect / briefing / backfill 接到同一执行语义上

## Capabilities Affected

### New Capabilities

- `research-web-jobs`: 约束本地任务模型、任务状态、日志和历史视图

### Modified Capabilities

- `research-web-collection`: 采集表单改为提交 job，而不是直接吞掉执行过程
- `research-web-workspace`: Dashboard 和其他页面需要展示任务状态摘要
- `research-operations`: 本地 Web 表面开始承接任务化执行语义

## Impact

- 影响范围：新的 job service / storage、Web API、Collect / Dashboard / Briefing 页面
- 建议优先级：P0
- 建议顺序：4 / 10
- 依赖：`add-collect-workspace-shell` 作为入口壳层；是 schedule 和 source-specific collect form 的共同前置

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 初期 jobs 可以先是本地单机进程内能力，不要求第一版就支持跨进程恢复或复杂并发编排
