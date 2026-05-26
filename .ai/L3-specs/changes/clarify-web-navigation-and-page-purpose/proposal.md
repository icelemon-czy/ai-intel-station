# clarify-web-navigation-and-page-purpose

> **状态**: drafting
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户要求把 Web 二期需求拆成多个可 review 的 change proposal，先写入仓库供筛选

## Why

当前 Web 导航直接使用 `Dashboard`、`Library`、`Briefing Workspace` 这类工程视角命名，但页面本身没有解释“这个页面解决什么问题、不解决什么问题”。结果是用户进入后无法区分“资料总览”、“本地检索”和“简报生成”，更容易把页面误解成采集控制台。

既然 Web 已经开始承接整项目的交互层，页面命名和用途说明就不能继续停留在内部实现语言，而要先解决认知成本和入口误导。

## What Changes

- 重命名或细化当前 Web 导航文案，使页面名称更贴近用户目标而不是内部实现术语
- 为每个页面增加一句话用途说明，明确“做什么 / 不做什么”
- 在关键页面加入下一步 CTA，例如“去采集”“去生成简报”“查看资料库”
- 同步更新 README、`.ai` 导航和前端文案，避免 CLI / Web / 文档三处描述分叉

## Alternatives Considered

1. **保留当前命名，只在 README 里补说明** — 改动最小，但用户真正看到页面时仍然会迷失
2. **统一改成更直白的页面命名并补页面内用途说明（当前选择）** — 同时解决导航语义和页面解释两个问题，成本可控

## Capabilities Affected

### New Capabilities

- `research-web-information-architecture`: 约束 Web 页面命名、页面用途说明和导航语义的一致性

### Modified Capabilities

- `research-web-workspace`: 调整首期 Web 导航的命名、说明和入口引导

## Impact

- 影响范围：`web/src/App.jsx`、前端文案、README、`.ai` 导航
- 建议优先级：P0
- 建议顺序：1 / 10
- 依赖：`add-react-web-workspace-mvp` 归档后进入；可独立于采集和 jobs 实现

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 仅解决认知和入口表达，不解决采集入口、jobs 或调度能力缺失
