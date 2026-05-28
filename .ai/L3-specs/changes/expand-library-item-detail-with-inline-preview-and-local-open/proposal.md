# expand-library-item-detail-with-inline-preview-and-local-open

> **状态**: pending-review
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

- `2026-05-29 00:00` — `—` → `drafting` by `/new-change` | 原因: 用户指出 Library item detail 信息过薄，希望补齐 inline preview 和本地文件打开动作

## Why

当前 Item detail 只展示标题、摘要、source、authors、tags、archive path 和一个 source link。对于“本地优先”的资料工作台来说，这个层次过浅，用户仍然需要跳出当前页面去翻本地 Markdown，无法完成高效比对和快速判断。

既然 Library 已经承担“检索 + 详情”职责，详情区就不应该只是一张 metadata 卡片，而应成为查看本地归档内容、理解来源背景和执行后续动作的操作面板。

## What Changes

- 扩充 Item detail，展示更多已有 metadata，例如 `item_type`、`published_at`、`updated_at`、`canonical_url` 和 source-specific metadata
- 增加“Quick preview”动作，在当前页面以内联浮层或侧滑面板形式展示本地 Markdown/摘要/关键元数据，而不是直接跳走
- 增加“Open local folder”或等价本地动作，让用户能从 Web 快速跳到本地归档目录
- 保持现有 “Open source link” 动作，但将其从唯一出口降级为多个 detail 动作之一

## Alternatives Considered

1. **只保留 source link，要求用户去 Finder 或编辑器里自己找文件** — 实现最小，但与“本地工作台”目标相悖，详情面板仍然偏空
2. **在当前页面补充 rich detail + inline preview + 本地打开动作（当前选择）** — 最符合资料浏览和后续处理的一体化体验

## Capabilities Affected

### New Capabilities

- `research-web-library-detail-preview`: 定义 Library item 的内联预览和详情展开行为
- `research-web-local-open-actions`: 定义从 Web 触发本地归档打开动作的约束与边界

### Modified Capabilities

- `research-web-workspace`: 将 Library detail 从轻量 metadata 卡片提升为可操作的详情面板

## Impact

- 影响范围：`web/src/App.jsx`、`web/src/styles.css`、`workspace_web/service.py`、`workspace_web/server.py`、`tests/test_web_workspace.py`
- 建议优先级：P0
- 建议顺序：2 / 3
- 依赖：建议在分页/选中态稳定后接入，避免 detail 预览先增强但用户仍然不清楚当前选中了哪一项

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 该提案不改变 collect、query 或 briefing 的业务规则，只强化 Library 的查看与操作能力
