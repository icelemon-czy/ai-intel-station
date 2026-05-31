# align-web-source-labels-between-library-and-collect

> **状态**: approved
> **创建**: 2026-05-29
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

- `2026-05-29 00:00` — `—` → `drafting` by `/new-change` | 原因: 用户指出 Library 中的 `papers` 与 Collect 中的 `arXiv` 命名不对齐，需要统一来源语义

## Why

当前同一个来源在不同页面用不同标签出现：Library 和内部 source id 使用 `papers`，Collect Workspace 却展示 `arXiv Papers`。这种命名漂移会让用户误以为这是两个不同来源，尤其会干扰筛选、采集和 briefing 之间的心智映射。

来源标签是整个工作台的基础语义，不应该在页面之间各自命名。否则后续再加 dashboard 指标、briefing 过滤或 jobs history，会继续放大概念漂移。

## What Changes

- 为 Web 工作台定义统一的 source label policy，明确哪些是内部 id，哪些是用户可见标签
- 对齐 Library、Collect、Dashboard、Briefing 中的 `github` / `papers` / `wechat` 显示文案
- 保持内部 source id 稳定，避免把 `papers` 直接改成破坏性更高的 `arxiv`
- 增加回归校验，防止同一 source 在不同页面再次出现标签漂移

## Alternatives Considered

1. **继续让各页面按自己的上下文起名字** — 文案更自由，但会持续制造“是不是两个来源”的歧义
2. **保持内部 id 不变，只统一用户可见标签（当前选择）** — 风险最小，也最容易在现有数据结构上落地

## Capabilities Affected

### New Capabilities

- `research-web-source-taxonomy`: 定义 Web 工作台的来源标签、内部 id 和展示文案边界

### Modified Capabilities

- `research-web-workspace`: 统一跨页面来源语言
- `research-web-collection`: 对齐 Collect Workspace 的 source 文案与 Library/Briefing 一致
- `papers`: 明确 Web 场景下的来源展示名与内部 source id 的关系

## Impact

- 影响范围：`workspace_web/service.py`、`web/src/App.jsx`、`tests/test_web_workspace.py`、Web 文案与相关 `.ai` 文档
- 建议优先级：P1
- 建议顺序：3 / 3
- 依赖：无硬依赖；可独立执行，也可与 `refresh-web-workspace-after-collect-run` 一起纳入 Collect 收口批次

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案只处理命名和标签对齐，不包含来源数据结构迁移或 archive 路径改名
