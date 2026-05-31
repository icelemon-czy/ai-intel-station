# add-scheduled-collection-and-refresh-policies

> **状态**: approved

## Review Feedback

- [x] 2026-06-01 review-tests: delta spec 占位符已补全，测试全绿
> **创建**: 2026-05-27
> **父变更** (parent-change): add-local-job-runner-and-job-history
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户明确提出“定时采样”诉求，本提案用于单独评估 schedule 和 refresh policy 的系统边界

## Why

当前系统边界明确排除了 `Scheduled background execution`，而用户现在已经明确提出定时采样 / 刷新需求。这意味着 schedule 不只是 Web 上多一个控件，而是会触及系统边界、执行方式和 jobs 模型。

因为它影响到 system 级边界，所以必须单独拆成一个提案，而不能作为 Collect Workspace 的附属小功能带过去。

## What Changes

- 新增定时采集和刷新策略的配置能力
- 支持定义按 source 或按任务模板的 schedule、下次运行时间和启停状态
- 把 schedule 接到本地 jobs 模型，而不是直接在 UI 层做伪状态
- 更新 system spec，明确是否将本地定时执行纳入系统边界，以及默认如何运行

## Alternatives Considered

1. **继续坚持完全无 schedule，只保留手动 Run now** — 系统边界最简单，但无法满足用户明确提出的定时采样诉求
2. **把 schedule 独立建模并修改 system 边界（当前选择）** — 风险更大，但能正面回应新的产品方向

## Capabilities Affected

### New Capabilities

- `research-web-scheduling`: 约束 schedule 模型、刷新策略和下次执行可视化

### Modified Capabilities

- `research-web-jobs`: jobs 模型需要支持定时触发和未来执行
- `system`: 系统边界需要从“无定时后台执行”调整为“支持本地定时执行”的新描述

## Impact

- 影响范围：system spec、本地任务调度、UI 配置页、jobs 执行链路
- 建议优先级：P2
- 建议顺序：10 / 10
- 依赖：强依赖 `add-local-job-runner-and-job-history`；推荐在手动 collect 和 diagnostics 稳定后再做

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案是系统级边界调整，不建议与其他 UI 文案或样式改动混做
