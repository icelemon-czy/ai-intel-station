# align-web-collect-with-local-output-truth

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

- `2026-05-27 00:18` — `—` → `drafting` by `/new-change` | 原因: Web 已出现 Collect Workspace
- `2026-05-27 01:00` — `drafting` → `implementing` by `/new-change` | 用户确认：加入
- `2026-05-27 01:10` — `implementing` → `pending-review` by `/new-change` | 29/29 测试全绿，但当前执行路径未稳定落到工作区 `output/` 真相源，需要独立提案收口

## Why

当前 Web collect 已经对用户可见，但 GitHub repo 模式写到 `/tmp/output`，GitHub search 与 papers 还是以内存结果为主，导致 Web 采集并不稳定地进入工作区归档真相源。这样一来，Dashboard / Library / Briefing 就无法可靠消费 Web 采集结果。

既然 Web 已开始承担 collect 入口，就必须保证它和 CLI 一样，把结果写回同一套 `output/` 目录边界，而不是走临时或只返回内存数据的分叉路径。

## What Changes

- 统一 Web collect 对 GitHub / papers / WeChat 的落盘目标，全部写入工作区真实 `output/` 根目录
- 移除或替换 `/tmp/output`、仅内存返回、只 fetch 不保存这类与 CLI 真相源脱节的执行路径
- 确保每个 source 的 Web collect 成功后都生成与 CLI 一致的 Markdown / sidecar 产物
- 明确 Web collect 与 CLI collect 的输出兼容性边界，避免同一 source 出现两套归档结构

## Alternatives Considered

1. **让 Web collect 保持预览态，不承诺写入本地 archive** — 改动更小，但会让 Web 看起来能 collect，实际上不能进入后续 Library / Briefing 工作流
2. **让 Web collect 与 CLI 共用同一 `output/` 真相源（当前选择）** — 保持系统边界一致，后续刷新、jobs 和 schedule 也有统一落点

## Capabilities Affected

### New Capabilities

- `research-web-collect-persistence`: 约束 Web collect 如何将 source-specific 结果落盘到本地 archive truth

### Modified Capabilities

- `research-web-collection`: 从“能提交采集”扩展为“能稳定写入工作区归档”
- `github`: Web repo/search 路径需要与 CLI 输出目录语义对齐
- `papers`: Web papers collect 需要从 fetch 扩展为落盘 sidecar / Markdown
- `wechat`: Web collect 成功后的归档结果需要与既有输出语义对齐

## Impact

- 影响范围：`workspace_web/service.py`、`collect/*` 调用方式、Web collect API、README / `.ai` 文档
- 建议优先级：P0
- 建议顺序：1 / 4
- 依赖：`add-collect-workspace-shell`、`add-wechat-url-collection-form`、`add-github-and-papers-collection-forms`

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只解决“写到哪里”和“是否进入真相源”，不直接解决 jobs history、schedule 或前端刷新联动
