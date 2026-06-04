# replace-library-file-url-with-safe-local-actions

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

- `2026-06-03 00:00` — [无] → [drafting] by /new-change | 原因: 当前 Library 直接从浏览器打开 `file://` 本地路径失败，需要定义可控、可理解的本地文件动作

## Why

当前 Item detail 的 `View Markdown` 按钮把相对 archive path 拼成 `file://` URL，既打不开，也没有向用户解释为什么失败。即使加入内联预览，Library 仍需要清晰区分“在 Web 内预览内容”和“对本地文件执行外部动作”。

本变更替换不可靠的 `file://` 行为，定义安全且可理解的本地动作边界。

## What Changes

- 移除或禁用前端直接拼接 `file://` 的 Markdown 打开方式。
- 将 detail actions 拆成明确语义：`Preview Markdown`、`Open source link`、`Copy archive path`，以及可选的 `Open local folder/file`。
- 如果支持打开本地 folder/file，则必须由后端执行受控动作，并限制目标在当前 `output_root` 内。
- 如果当前环境不支持打开本地 folder/file，则 UI 应给出明确状态，并提供复制路径作为可靠替代。
- 本变更不负责渲染 Markdown 正文；正文阅读由 `add-library-safe-markdown-preview` 提供。

## Alternatives Considered

1. **继续保留 `View Markdown` 并只修正绝对路径** — 仍会受浏览器 `file://` 安全策略影响，体验不稳定。
2. **完全删除本地文件动作** — 最简单，但本地优先工具需要让用户能回到文件系统或编辑器。
3. **用明确 actions 替换 `file://`，复制路径作为保底（当前选择）** — 先保证所有环境可用，再按需支持受控的系统打开动作。

## Capabilities Affected

### New Capabilities

- `research-web-library-local-actions`: 定义 Library detail 中本地路径复制、外部打开动作和不可用状态的行为边界。

### Modified Capabilities

- `research-web-workspace`: 移除 Library detail 中不可靠的浏览器 `file://` 打开模式。

## Impact

- 影响范围：`web/src/App.jsx`、`web/src/styles.css`，如支持后端打开动作则涉及 `workspace_web/service.py`、`workspace_web/server.py` 和 `tests/test_web_workspace.py`。
- 不改变 sidecar 格式、不改变 Markdown 文件路径、不改变 collect/query/briefing 业务规则。
- 需要明确 macOS、本地浏览器和无系统打开能力时的行为差异。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不负责读取和展示 Markdown 内容；该能力由 `add-library-safe-markdown-preview` 承担。
- [ ] 不承诺跨平台系统打开能力；如业务确认需要，后续 spec 将定义平台支持和失败提示。