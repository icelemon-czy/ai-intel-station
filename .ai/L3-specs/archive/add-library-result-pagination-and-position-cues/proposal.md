# add-library-result-pagination-and-position-cues

> **状态**: approved
> **创建**: 2026-05-29
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

- `2026-05-29 00:00` — `—` → `drafting` by `/new-change` | 原因: 用户明确要求 Library results 支持分页，并希望在结果规模增大时保持可定位的浏览体验

## Why

当前 Library 会把全部结果一次性渲染出来。随着本地 archive 变大，结果列表会快速失控：用户不知道当前是在第几页、第几条，也难以回到刚才看过的位置。

分页不是纯视觉优化，而是 Library 从“演示级列表”进入“可持续浏览界面”的基础门槛。尤其在已有选中态需求存在的前提下，分页和位置提示必须一起补齐，才能让用户稳定地浏览几十到几百条结果。

## What Changes

- 为 Library results 引入分页能力，支持页码切换、每页数量和总条数显示
- 在结果区和详情区同时显示当前浏览位置，例如“第 2 页 / 共 18 页”“当前第 17 条 / 共 243 条”
- 约束搜索、翻页、重新筛选后的选中项行为，避免详情面板与列表位置失联
- 允许在实现阶段评估成熟 React 分页库，但不强制引入重型表格框架

## Alternatives Considered

1. **继续一次性渲染全部结果，只靠滚动浏览** — 最省实现，但结果一多就会失去位置感，也无法建立稳定的浏览节奏
2. **改成显式分页 + 位置提示（当前选择）** — 交互清晰，最符合本地资料库长期增长后的使用方式

## Capabilities Affected

### New Capabilities

- `research-web-library-pagination`: 定义 Library 结果的分页、页码和位置信息要求

### Modified Capabilities

- `research-web-workspace`: 将 Library 从单屏结果列表扩展为支持分页的浏览工作区
- `research-web-library-interaction`: 约束分页与选中项、详情面板之间的同步行为

## Impact

- 影响范围：`web/src/App.jsx`、`web/src/styles.css`、`workspace_web/service.py`、`workspace_web/server.py`、`tests/test_web_workspace.py`
- 建议优先级：P0
- 建议顺序：1 / 3
- 依赖：建议与现有 `add-library-selection-state-and-active-styling` 一起评估，避免分页先落地但仍看不出当前选中项

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只解决分页与位置提示，不包含更丰富的详情内容或本地文件操作
