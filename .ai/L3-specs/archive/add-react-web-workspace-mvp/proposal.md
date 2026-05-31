# add-react-web-workspace-mvp

> **状态**: approved
> **创建**: 2026-05-25
> **父变更** (parent-change): restructure-research-architecture
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

- `2026-05-25 18:57` — `—` → `drafting` by `/new-change` | 原因: 用户要求为第一期 React Web 交互页面建立 L3 级需求提案，并先明确范围边界与业务确认问题
- `2026-05-25 19:32` — `drafting` → `implementing` by `/new-change` | 原因: 用户通过 `/continue-change 1` 选择继续该提案，本轮按 proposal 默认边界确认第一期仅包含 Dashboard / Library / Briefing Workspace，保持单机单用户与 CLI/output 真相源约束
- `2026-05-31` — `pending-review` → `review-failed` by `/review-tests` | 原因: REQ-4 Scenario 要求 MVP 不暴露 collect，但测试期望 collect 存在，违反 delta spec
- `2026-05-31` — `review-failed` → `pending-review` by `/fix-bug` | 原因: 已更新 delta spec REQ-4 将 collect 纳入 MVP scope，测试同步修正

## Why

当前项目的 collect、query、briefing、backfill 已经形成统一 CLI 和本地 sidecar 流程，但日常使用仍然依赖记命令、看目录和手动判断结果。对“按主题浏览资料、筛选本地归档、预览 briefing、判断当前资料库状态”这类高频操作来说，CLI 已经够做系统底座，不够做稳定交互层。

现在引入第一期 React Web，不是为了重做采集逻辑，而是为了把已经存在的本地能力收束成一个可持续使用的本地工作台。这样既能复用现有 output 和 sidecar 体系，也能为后续任务执行、环境诊断和更完整的操作流留出清晰边界。

## What Changes

- 新增一个本地优先的 React Web 工作台，作为 AI Intel Station 的第一期交互层
- 第一阶段聚焦 3 个高频使用场景：Dashboard、Library、Briefing Workspace
- Dashboard 展示本地归档概况、来源覆盖、最近 briefing 产物、缺失 sidecar / 缺失来源等可读状态
- Library 提供基于现有 sidecar 的关键词检索、来源过滤、时间过滤、结果列表和详情查看
- Briefing Workspace 支持选择模式、输入查询条件、预览结果并保存到 `output/briefing/`
- Web 层继续以本地归档和 sidecar 为事实来源，不改变 `output/github`、`output/papers`、`output/wechat` 与 `output/briefing/` 的边界
- 第一阶段暂不包含采集执行、backfill 执行、多用户、远程部署、认证鉴权和向量检索

## Alternatives Considered

1. **只做静态展示页或 README 导航页** — 实现最快，但无法解决“浏览资料、筛选结果、预览 briefing”这些真实高频操作
2. **一步做到完整 Web 控制台（含 collect、backfill、任务调度、账号体系）** — 看起来完整，但会过早把范围扩展到本地任务编排和长期运行时，第一阶段风险过大
3. **先做本地优先的 React Web MVP（当前选择）** — 先把最常用的读取、筛选和 briefing 生成体验补齐，同时继续复用现有 CLI、output 和 sidecar 作为系统真相源

## Capabilities Affected

### New Capabilities

- `research-web-workspace`: 提供本地 React Web 工作台，用于展示资料库状态、浏览 ResearchItem、配置并生成 briefing

### Modified Capabilities

- `system`: 系统边界从“本地 CLI 工作区”扩展为“本地 CLI + 本地 Web 工作台”，但仍不把远程 API 服务、多用户协作和定时后台任务纳入当前边界

## Impact

影响范围会覆盖新的前端工作区、一个仅服务本地界面的桥接层、现有 query / briefing 能力的可视化编排方式，以及 `.ai` 文档、spec 和验证说明。

这次 proposal 默认守住 4 个约束：

- CLI 仍然保留，并继续作为稳定的 operator surface
- Web 不直接绕过 sidecar 和 output 规则去发明第二套数据真相
- 第一阶段优先做“读、筛、预览、生成”，不把 collect / backfill 任务控制台塞进同一轮
- 现有历史归档应尽量直接可用，必要时允许通过 backfill 补齐 sidecar，而不是要求迁移旧目录结构

## Review Feedback

- [x] 2026-05-31 review-tests: REQ-4 Scenario "Open the phase-one web navigation" spec 与实现矛盾。delta spec 要求 MVP 不暴露 collect，但测试 `test_workspace_sections_match_phase_one_scope` 期望 collect 存在。proposal 正文"第一阶段暂不包含采集执行"与 delta spec 描述一致。根因：delta spec REQ-4 禁止 collect 是正确的，但测试写于早期，基于旧版 scope 假设。已更新 delta spec REQ-4 明确纳入 collect workspace，确认 spec 是最终约束；测试已修正以反映 REQ-4 的 MVP scope。

## Known Gaps

- [ ] 本提案默认第一阶段不包含 collect / backfill 的 Web 执行入口；若你希望一期就做任务控制台，需要在确认时显式扩大范围
- [ ] 本提案默认单机单用户；若你希望未来支持远程访问或多人共享，需要在系统边界里提前写明
