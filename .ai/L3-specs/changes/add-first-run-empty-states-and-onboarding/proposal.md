# add-first-run-empty-states-and-onboarding

> **状态**: pending-review
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

- `2026-05-27 00:04` — `—` → `drafting` by `/new-change` | 原因: 当前 Web 在空资料库场景下缺少引导，用户要求把首次使用和空状态体验单独提案

## Why

当前 Web 默认假设本地已经有 sidecar 和 briefing，因此在“刚打开、还没采集任何内容”的场景下，只能看到空面板、0 条统计或无法理解的控件。对新用户而言，这相当于系统没有告诉他第一步该做什么。

如果 Web 真要成为整个项目的交互层，就必须显式处理首次使用、无数据、部分数据和缺 sidecar 这几类高频空状态。

## What Changes

- 为 Dashboard、Library、Briefing、未来的 Collect Workspace 增加空状态文案和下一步引导
- 增加首次进入时的 onboarding 提示，说明“先采集、再检索、再生成 briefing”的基本流程
- 针对无数据、缺 sidecar、缺 briefing 产物等场景提供不同文案和 CTA
- 把空状态设计与页面用途说明联动，避免页面在无数据时看起来像故障

## Alternatives Considered

1. **等 Collect Workspace 做完后再统一处理空状态** — 能少改一次，但当前页面会继续对新用户很不友好
2. **先独立补齐首次使用和空状态引导（当前选择）** — 即使采集页还没上线，也能让用户知道系统下一步应做什么

## Capabilities Affected

### New Capabilities

- `research-web-onboarding`: 约束首次使用引导、空状态文案和下一步 CTA

### Modified Capabilities

- `research-web-workspace`: 为现有页面补首次使用和无数据场景的可解释性

## Impact

- 影响范围：`web/src/App.jsx`、前端文案、可能新增 onboarding 状态存储
- 建议优先级：P1
- 建议顺序：9 / 10
- 依赖：推荐在 `add-collect-workspace-shell` 之后实施，以便 CTA 可直接指向采集页

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不负责真正采集数据，只负责在空状态下把用户引到正确的下一步
