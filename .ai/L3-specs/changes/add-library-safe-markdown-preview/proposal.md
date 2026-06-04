# add-library-safe-markdown-preview

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

- `2026-06-03 00:00` — [无] → [drafting] by /new-change | 原因: 用户指出 Item detail 中 View Markdown 不合理，需要在 Web 内安全查看本地 Markdown 内容

## Why

当前 `View Markdown` 依赖前端拼接 `file://` 打开本地相对路径，在浏览器安全模型下会被拦截，用户无法在 Library 中查看已归档 Markdown。Library 作为本地资料库入口，应能在同一界面读取并预览 output 下的 Markdown 内容。

本变更把 Markdown 查看从不可靠的浏览器本地文件跳转改为后端受控读取 + 前端内联预览。

## What Changes

- 新增 Library Markdown preview 能力：根据选中 item 的 `output_path` 读取对应本地 Markdown 内容并返回给前端。
- 在 Item detail 中提供 Markdown preview 区域或 tab，让用户不离开 Library 即可阅读归档正文。
- 后端读取必须限制在当前 `output_root` 内，并且只允许读取 item sidecar 已知的 Markdown 路径，防止任意文件读取。
- 对 Markdown 缺失、路径非法、文件不可读等场景返回明确错误状态，前端展示可理解的失败信息。
- Preview 不修改文件、不触发 collect、不生成 briefing，只读取本地 archive 中已有内容。

## Alternatives Considered

1. **继续用 `file://` 打开 Markdown** — 实现简单，但当前浏览器已经拦截，且相对路径不可靠。
2. **只显示 archive path，让用户手动去编辑器打开** — 安全但体验退化，Library 仍无法完成阅读闭环。
3. **后端受控读取 + 前端内联预览（当前选择）** — 符合 local-first 边界，也能建立可测试的路径安全约束。

## Capabilities Affected

### New Capabilities

- `research-web-library-markdown-preview`: 定义 Library 中安全读取和内联预览本地 Markdown 的行为。

### Modified Capabilities

- `research-web-workspace`: 将 Library detail 从 metadata 查看扩展为可阅读本地归档正文。

## Impact

- 影响范围：`workspace_web/service.py`、`workspace_web/server.py`、`web/src/App.jsx`、`web/src/styles.css`、`tests/test_web_workspace.py`。
- 需要新增 API 或扩展 item detail payload，但不改变现有 `/api/library` 查询语义。
- 需要测试路径安全、文件缺失和正常预览三类场景。
- 不涉及数据迁移，不涉及远程网络访问，不涉及 collect 或 briefing 业务规则。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不负责重新设计 Library 整体排版；该能力由 `redesign-library-search-inspection-layout` 承担。
- [ ] 不负责打开系统默认应用或 Finder；该能力由 `replace-library-file-url-with-safe-local-actions` 承担。
