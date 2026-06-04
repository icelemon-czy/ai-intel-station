# Add First Run Empty State Guidance

> **状态**: approved
> **创建**: 2026-06-01
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

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
|:-----|:-----|:---------|
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal）|
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿）|
| pending-review | review-failed | /review-tests（打回）|
| review-failed | implementing | /fix-bug（开始修）|
| pending-review | approved | /review-tests（通过）|
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建首次使用和空状态引导 proposal，等待业务确认
- `2026-06-01 12:35` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进，AI 接管
- `2026-06-01 13:00` — [implementing] → [pending-review] by /continue-change | 原因: 4 个新测试全绿 + 45/45 tests/test_web_workspace.py 绿灯

## Why

Web 工作台第一次打开或筛选结果为空时，当前界面容易让用户误以为系统异常，或者不知道下一步应该 collect、backfill、调整筛选还是生成 briefing。

本变更为主要页面增加 first-run / empty-state 引导，让空数据状态也能给出明确解释和下一步动作。

## What Changes

- Dashboard 在本地资料库为空时展示清晰空状态：说明当前还没有可读 ResearchItem，并提示可先去 Collect Workspace 或运行 backfill。
- Library 在无搜索结果时展示空状态：说明当前只搜索本地归档，并提示调整关键词、来源、日期范围或先收集资料。
- Briefing Workspace 在没有可用资料或 preview 为空时展示空状态：说明 briefing 依赖本地资料库，提示先 collect / backfill / 调整筛选。
- Collect Workspace 在尚未运行收集时展示起步提示：说明选择来源、填写输入、手动运行后资料会进入本地归档。
- 空状态应是页面内提示，不新增弹窗、向导、账户状态、远程 onboarding 或持久化偏好。
- 不改变查询、采集、briefing 生成逻辑，也不修改 `output/` 中已有内容。

## Alternatives Considered

1. **做完整 onboarding 向导** — 能覆盖更多新手路径，但交互和状态管理范围太大。
2. **只在 README 里补说明** — 维护成本低，但无法解决用户在页面内看到空白状态时的即时困惑。
3. **页面内空状态引导（当前选择）** — 作用直接、实现小，并能覆盖首次使用和日常无结果两种高频场景。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Web 工作台主要页面在空数据、无结果或未运行状态下应展示解释性引导和下一步动作。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- 回归测试：`tests/test_web_workspace.py` 可增加 Dashboard / Library / Briefing / Collect 空状态关键文案断言。
- 不涉及后端 API 合约、输出路径、数据迁移或外部依赖。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不包含完整 glossary 或帮助中心；术语解释可在后续独立变更处理。
- [ ] 不包含 Collect job history、schedule 或 runtime diagnostics 的空状态，这些应随对应功能变更处理。
