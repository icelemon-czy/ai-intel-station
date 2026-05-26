# add-github-and-papers-collection-forms

> **状态**: drafting
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户要求把 GitHub / papers 采集输入也纳入 Web，而不是继续停留在本地 CLI

## Why

GitHub 和 papers 也都不是单一输入模型。GitHub 至少区分 `owner/repo` 和 search query，papers 则区分类别白名单和 `max`。如果继续只给一个抽象输入框，用户既不知道填什么，也无法得到 source-specific 校验。

因此在 Collect Workspace 建立后，需要尽快把 GitHub 和 papers 表单分别补齐，形成与 WeChat 并列的 source-specific 采集入口。

## What Changes

- 为 GitHub 增加 repo 模式和 search 模式两类输入表单
- 为 papers 增加 category 选择、多 category 支持和 `max` 输入
- 为 GitHub / papers 增加 source-specific 校验和错误提示
- 把三类 source 的输入表面统一收进 Collect Workspace，但保持各自字段独立

## Alternatives Considered

1. **先只做 WeChat，把其他 source 继续留在 CLI** — 可先满足 URL 场景，但 Web 仍然不是完整采集入口
2. **补 GitHub / papers 的 source-specific 表单（当前选择）** — 让 Web 真正开始承接 collect 能力，但仍保持 source 差异清晰

## Capabilities Affected

### New Capabilities

- `research-web-github-papers-collection`: 定义 GitHub / papers 在 Web 中的表单、校验和反馈行为

### Modified Capabilities

- `research-web-collection`: 将 Collect Workspace 从壳层扩展到多 source 可用表面
- `github`: 明确 Web 场景下的 repo/search 输入契约
- `papers`: 明确 Web 场景下的 category/max 输入契约

## Impact

- 影响范围：Collect Workspace、GitHub / papers 表单、错误提示、CLI / Web 文档
- 建议优先级：P1
- 建议顺序：6 / 10
- 依赖：`add-collect-workspace-shell`；推荐在 `add-local-job-runner-and-job-history` 之后接入执行链路

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不处理 schedule，也不包含 WeChat 的 URL 驱动交互细节
