# add-collect-workspace-ui-regression-coverage

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

- `2026-05-27 00:18` — `—` → `drafting` by `/new-change` | 原因: collect 导航和 API 已存在
- `2026-05-27 01:00` — `drafting` → `implementing` by `/new-change` | 用户确认：加入
- `2026-05-27 01:10` — `implementing` → `pending-review` by `/new-change` | 29/29 测试全绿，但前端渲染分支曾经缺失，需要独立提案补足回归覆盖

## Why

这次 collect 能力之所以在 Web 上“看起来做了、页面里却找不到”，根因不是 API 没做，而是 React 主界面没有把 `collect` section 挂出来。现有测试主要覆盖 service 和 API，没有约束前端导航项和实际渲染分支必须一致。

只要这一层没有回归覆盖，后面 jobs、schedule、diagnostics 也都可能再次出现“后端有，前端没挂”的假完成状态。

## What Changes

- 为 Collect Workspace 增加前端回归测试，覆盖导航项存在、页面壳层渲染、source 切换和提交入口存在
- 增加“导航声明的 section 必须在 `App.jsx` 有对应渲染分支”的验证
- 补一个面向工作台的 smoke 验证，防止静态构建成功但页面入口缺失
- 将这类前端渲染覆盖纳入 Web workspace 的 traceability，而不是只验证后端 service

## Alternatives Considered

1. **继续只测 service / API，不测 React 渲染分支** — 现有成本最低，但已经证明抓不到“导航有、页面没挂”的真实回归
2. **补充前端回归覆盖（当前选择）** — 需要引入或收紧前端 smoke 方式，但能显著降低假完成风险

## Capabilities Affected

### New Capabilities

- `research-web-ui-regression-coverage`: 约束 Web workspace 的前端渲染与导航一致性验证

### Modified Capabilities

- `research-web-workspace`: 从只验证 API / service 扩展为验证 React 入口渲染闭环

## Impact

- 影响范围：前端测试栈或 smoke 验证脚本、`web/src/App.jsx`、`tests/test_web_workspace.py` 或新的 Web 验证文件、traceability
- 建议优先级：P1
- 建议顺序：4 / 4
- 依赖：`add-collect-workspace-shell`；可与其他 collect 能力并行实施

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只降低“前端没挂出来”的回归风险，不直接提供新的用户功能
