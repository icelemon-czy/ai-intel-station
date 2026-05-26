# add-collect-workspace-shell

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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 用户指出 Web 没有立即采集入口，需要先建立独立的 Collect Workspace 框架提案

## Why

现在的 Web 只能浏览本地已有资料、生成 briefing，却没有“把资料抓进来”的主入口。这意味着 Web 还只是已有 CLI 能力的查看器，而不是整个项目的交互台。

如果要让 Web 成为整项目的工作台，就必须先有一个独立的 Collect Workspace，哪怕第一步只是页壳、source 切换和结果区域。

## What Changes

- 新增独立的 Collect Workspace 页面和导航入口
- 在页面内提供 source 切换、输入区域、运行状态区域和结果摘要区域
- 先建立统一页壳和交互框架，再让各 source 表单逐个接入
- 与 Dashboard、Library、Briefing 的导航语义和页面说明保持一致

## Alternatives Considered

1. **直接把采集按钮塞进 Dashboard 或 Briefing 页面** — 改动最少，但信息架构会迅速混乱
2. **先建立独立 Collect Workspace 壳层（当前选择）** — 先把采集作为一级能力放正，再分 source 补细节

## Capabilities Affected

### New Capabilities

- `research-web-collection`: 定义 Web 中面向采集任务的独立交互页面和统一入口

### Modified Capabilities

- `research-web-workspace`: 将 Web 导航从“看本地数据”扩展为“看 + 采 + 出简报”三类工作流
- `research-operations`: 扩展统一入口对 Web 采集表面的承载方式

## Impact

- 影响范围：`web/src/App.jsx`、新的 collect API / service、页面导航、说明文档
- 建议优先级：P0
- 建议顺序：3 / 10
- 依赖：`add-react-web-workspace-mvp`；是后续 WeChat / GitHub / papers 表单与 jobs 的前置壳层

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只建立采集工作台框架，不负责一次性补齐所有 source 的字段和任务执行细节
