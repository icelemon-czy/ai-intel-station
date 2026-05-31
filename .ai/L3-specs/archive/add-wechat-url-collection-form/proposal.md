# add-wechat-url-collection-form

> **状态**: approved
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户明确指出 WeChat 采集必须提供 URL 输入，本提案拆出为 source-specific 表单 change

## Why

WeChat 采集不是抽象的“输入关键词就能跑”，而是明确依赖文章 URL、URL 归一化、浏览器运行时和真实网络抓取。当前 Web 连 URL 输入框都没有，等于没有提供 WeChat 采集能力。

由于 WeChat 的输入模型和依赖前提都明显不同于 GitHub / papers，它值得作为独立 change 来设计和确认。

## What Changes

- 在 Collect Workspace 中新增 WeChat source 表单
- 支持单 URL 和批量 URL 输入，并在提交前做 URL 规范化和合法性校验
- 显示 WeChat 采集的前置条件、运行时提示和失败原因
- 在成功后展示 Markdown、images 和 sidecar 的落盘结果摘要

## Alternatives Considered

1. **把 WeChat 和 GitHub / papers 统一成一套抽象表单** — 表面统一，但会隐藏 WeChat 的真实约束，后续错误处理更混乱
2. **单独为 WeChat 设计 URL 驱动的采集表单（当前选择）** — 直接贴近现有运行语义，也更容易做错误提示

## Capabilities Affected

### New Capabilities

- `research-web-wechat-collection`: 约束 WeChat URL 输入、校验、执行反馈和结果展示

### Modified Capabilities

- `research-web-collection`: 在采集工作台中增加 WeChat source-specific 交互
- `wechat`: 扩展到 Web 表面所需的输入校验和结果反馈契约

## Impact

- 影响范围：Collect Workspace、WeChat 表单、输入校验、错误反馈、文档
- 建议优先级：P0
- 建议顺序：5 / 10
- 依赖：强依赖 `add-collect-workspace-shell`；推荐与 `add-local-job-runner-and-job-history` 配合落地

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不负责 GitHub / papers 的 source-specific 表单，也不自动补齐 schedule 能力
