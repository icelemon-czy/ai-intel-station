# Add Collect Source Purpose Cards

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

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建 Collect 来源用途卡片 proposal，等待业务确认
- `2026-06-01 12:00` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进，AI 接管 spec + 测试 + 代码实施
- `2026-06-01 12:30` — [implementing] → [pending-review] by /continue-change | 原因: 4 个新测试全绿 + 41/41 tests/test_web_workspace.py 绿灯，等 Reviewer 审查

## Why

Collect Workspace 支持 GitHub、arXiv Papers、WeChat 三类来源，但各来源输入、依赖和输出含义不同，用户切换来源时缺少足够的上下文。

本变更为每个 collect source 增加用途卡片，帮助用户在运行前理解“适合收集什么、需要填什么、结果写到哪里”。

## What Changes

- 为 GitHub source 展示用途卡片：适合仓库快照或搜索结果，输入 owner/repo 或搜索关键词，输出到 `output/github/`。
- 为 arXiv Papers source 展示用途卡片：适合按类别拉取论文摘要，输入 arXiv category 和 max results，输出到 `output/papers/`。
- 为 WeChat source 展示用途卡片：适合抓取公众号文章，输入文章 URL，输出到 `output/wechat/`。
- 每张卡片可包含 source purpose、required input、local output、external dependency / failure hint 等短信息。
- 卡片随 active source 切换更新，作为表单旁的解释层，不新增新的 collect source。
- 不改变 collect 后端执行逻辑，不新增 schedule、job queue、credential 管理或远程状态检测。

## Alternatives Considered

1. **把所有说明塞进字段 placeholder** — 改动小，但信息空间不足，且不同来源的输出和依赖解释会变得拥挤。
2. **做全局 Collect 帮助页** — 可承载更多内容，但用户切换来源时仍需要跳转理解。
3. **随来源切换的用途卡片（当前选择）** — 信息就地出现，和表单输入保持上下文一致。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Collect Workspace 应为每个支持的来源展示用途、输入、输出目录和关键依赖提示。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- 服务层元数据：若现有 `/api/collect/form/:source` 描述不足，可在 `workspace_web/service.py` 的 form metadata 中补充说明字段。
- 回归测试：`tests/test_web_workspace.py` 可增加 collect source metadata 或 UI 文案断言。
- 不涉及真实采集逻辑、输出格式、外部依赖安装或认证流程。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不实现运行前 preflight checks；依赖诊断可在 runtime diagnostics 变更中处理。
- [ ] 不新增 job history、schedule 或 refresh policy 控件。
