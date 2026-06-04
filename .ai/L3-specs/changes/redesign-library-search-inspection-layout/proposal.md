# redesign-library-search-inspection-layout

> **状态**: pending-review
> **创建**: 2026-06-03
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

- `2026-06-03 00:00` — [无] → [drafting] by /new-change | 原因: 用户指出 Library UI 排版不合理，需要将检索、扫读和详情查看重新组织为可用的资料库工作台

## Why

当前 Library 把页面说明、搜索表单、结果列表和详情面板压成三栏，核心任务“快速筛选、扫读结果、检查选中项”被稀释。随着本地 archive 增长，现有排版会让结果列表过窄、详情信息拥挤、说明文字占据过多首屏空间。

这个变更将 Library 从展示型三栏页面调整为检索工作台，让结果和详情成为主界面主体。

## What Changes

- 将 Library 搜索条件从左侧大表单收敛为顶部 filter bar，包括 keyword、source、date range、search action 和结果统计。
- 将主区域调整为两栏结构：宽结果列表 + 选中项详情区，结果列表承担主要扫读空间。
- 将结果项改为紧凑、稳定的 row/card 样式，突出 source、title、summary、published/tags/path 等扫读信息。
- 将页面说明和 search scope 从主布局中降级为轻量状态文案或辅助说明，避免压过主要工作流。
- 重新组织详情区的信息层级，将标题、摘要、关键 metadata、archive path 和 actions 分组显示。
- 不改变 Library 的本地查询语义、分页 API、collect 行为或 briefing 行为。

## Alternatives Considered

1. **只微调现有三栏 CSS** — 改动较小，但无法解决三栏同权导致的主次错位，结果列表和详情仍然被挤压。
2. **引入完整 data table 框架** — 可能提供更强排序/列配置，但会显著扩大依赖和交互范围，超出当前本地资料库工作台需要。
3. **顶部筛选 + 两栏检索/详情工作台（当前选择）** — 保持实现边界可控，同时直接修复信息架构和扫读效率问题。

## Capabilities Affected

### New Capabilities

- `research-web-library-layout`: 定义 Library 的检索工作台布局、结果扫读区和详情区信息层级。

### Modified Capabilities

- `research-web-workspace`: 将 Library 页面从三栏展示卡片调整为以本地检索和资料检查为核心的工作台。

## Impact

- 影响范围：`web/src/App.jsx`、`web/src/styles.css`、`tests/test_web_workspace.py`，可能补充前端结构断言。
- 不涉及 `workspace_web/service.py` 查询语义变更，不涉及 `library/query.py`，不涉及数据迁移。
- 与 `clarify-library-local-search-scope` 兼容：本变更只改变说明出现的位置和重量，不删除本地搜索边界。
- 与已归档的分页/选中态需求兼容：本变更会吸收现有分页和 active state 作为布局中的基础元素。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不新增 Markdown 正文读取能力；该能力由后续 `add-library-safe-markdown-preview` 承担。
- [ ] 不新增系统级打开本地文件能力；该能力由后续 `replace-library-file-url-with-safe-local-actions` 承担。
