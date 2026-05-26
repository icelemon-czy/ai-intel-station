# add-runtime-diagnostics-and-preflight-checks

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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户指出 Web 采集前缺少 URL / 依赖 / 环境检查，需要单独提案承接 preflight 和 diagnostics

## Why

采集入口一旦进入 Web，就不能假设用户知道 `gh` 是否已登录、WeChat 浏览器依赖是否可用、URL 是否合法、输出目录是否可写。没有 preflight，用户只会看到含糊的失败结果，而不知道该修什么。

这类能力既影响采集执行前的校验，也影响 Dashboard/Collect 对系统状态的解释，因此应作为独立 change 明确建模。

## What Changes

- 新增运行时诊断页或诊断模块，展示依赖可用性、路径写入能力和 source-specific 前置条件
- 在提交 collect 之前做 preflight checks，例如 WeChat URL 合法性、GitHub CLI 状态、papers category 合法性
- 将错误提示从“失败了”提升为可定位的失败原因与建议动作
- 让 Dashboard 和 Collect Workspace 都能消费 diagnostics 结果

## Alternatives Considered

1. **先只显示通用错误消息，不做环境诊断** — 实现快，但 Web 采集一旦失败就很难让用户自助恢复
2. **把 diagnostics 与 preflight 当成独立能力补齐（当前选择）** — 增加一点基础设施，但能显著降低采集失败的模糊性

## Capabilities Affected

### New Capabilities

- `research-web-runtime-diagnostics`: 定义依赖检查、输入校验和失败解释能力

### Modified Capabilities

- `research-web-collection`: collect 提交前增加 source-specific preflight
- `wechat`: WeChat URL 和运行时前置条件需要明确暴露到 Web
- `github`: Web 场景下需要显式报告 `gh` 可用性和认证状态
- `papers`: Web 场景下需要显式报告 category 和参数合法性

## Impact

- 影响范围：Collect Workspace、Dashboard、运行时检查 API、错误反馈文案
- 建议优先级：P1
- 建议顺序：7 / 10
- 依赖：`add-collect-workspace-shell`；与 `add-local-job-runner-and-job-history` 强相关，但可先行实现 preflight

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] diagnostics 能提高可解释性，但不替代 source-specific collect form 和 jobs 历史能力
