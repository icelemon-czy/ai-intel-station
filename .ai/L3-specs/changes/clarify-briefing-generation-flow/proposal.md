# Clarify Briefing Generation Flow

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

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建 Briefing 生成流程说明 proposal，等待业务确认
- `2026-06-01 13:05` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进，AI 接管
- `2026-06-01 13:30` — [implementing] → [pending-review] by /continue-change | 原因: 4 个新测试全绿 + 49/49 tests/test_web_workspace.py 绿灯

## Why

Briefing Workspace 目前能 preview 和 save，但 digest、reading-list、preview、save 的区别不够直观，用户不容易判断按钮会不会写文件，以及生成内容来自哪里。

本变更补齐 Briefing 生成链路说明，让用户在生成前理解输入、模式、预览和保存产物。

## What Changes

- 在 Briefing Workspace 顶部或控制区说明：briefing 基于本地 Library / ResearchItem 生成，不重新抓取远程资料。
- 为 `digest` 和 `reading-list` 模式增加简短用途说明。
- 明确 Preview 与 Save 的差异：Preview 只展示派生 Markdown，Save 会写入 `output/briefing/`。
- 在保存成功后继续清晰展示保存路径，并说明该文件是派生阅读产物。
- 在没有预览内容或筛选不到资料时提供解释性提示。
- 不改变 digest / reading-list Markdown 格式，不改变保存路径，不新增新的 briefing 模式。

## Alternatives Considered

1. **重做 Briefing Workspace 成分步向导** — 能更强地引导流程，但会引入更重的交互和状态管理。
2. **只在按钮上改文案** — 能提示部分行为，但无法解释输入来源和模式差异。
3. **在现有控制区补充生成流程说明（当前选择）** — 保持当前工作流轻量，同时补上用户最容易误解的行为边界。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Briefing Workspace 应解释本地资料输入、briefing 模式、preview 与 save 的产出差异。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- 回归测试：`tests/test_web_workspace.py` 可增加 Briefing 模式说明和 preview / save 文案断言。
- 不涉及 `briefing/` Markdown 生成逻辑、`publish/obsidian.py`、输出路径或数据迁移。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不新增 briefing 模板管理、历史版本比较或 Obsidian 打开动作。
- [ ] 不处理 partial-success 结果展示的深层改造，后续可独立拆分。
