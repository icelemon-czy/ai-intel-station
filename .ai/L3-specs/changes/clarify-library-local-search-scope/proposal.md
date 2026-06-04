# Clarify Library Local Search Scope

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

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建 Library 本地搜索边界说明 proposal，等待业务确认
- `2026-06-01 13:35` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进
- `2026-06-01 14:00` — [implementing] → [pending-review] by /continue-change | 原因: 4 个新测试全绿 + 53/53 tests/test_web_workspace.py 绿灯

## Why

Library 页面容易被误解为远程搜索入口，但当前设计是读取本地 `output/` 下的 ResearchItem sidecar 并做本地筛选。

本变更专门澄清 Library 的搜索边界，避免用户以为搜索会触发 GitHub、arXiv 或 WeChat 的联网抓取。

## What Changes

- 在 Library 搜索区域增加简短说明：搜索范围是本地归档和 sidecar，而不是远程源。
- 在 Sources、Keyword、Since / Until 附近补充轻量提示，解释这些筛选只作用于已保存的 ResearchItem。
- 在结果列表或详情区域保留本地归档语义，明确结果来自 `output/` 中的已保存资料。
- 在无结果状态中提示用户可以调整本地筛选，或去 Collect Workspace 增加资料。
- 不新增远程搜索能力，不改变查询参数语义，不改变分页、排序、详情字段或 `library/query.py` 的筛选逻辑。

## Alternatives Considered

1. **把 Library 改成远程搜索 + 本地搜索混合入口** — 功能更强，但会破坏当前 local-first 边界并显著扩大失败模式。
2. **只改按钮文案为 Search** — 改动很小，但不足以解释数据来源和行为边界。
3. **在 Library 关键区域加入本地搜索说明（当前选择）** — 保持现有功能不变，同时降低误解成本。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Library 页面应清晰说明搜索只针对本地 ResearchItem / sidecar，不触发远程抓取。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- 回归测试：`tests/test_web_workspace.py` 可增加 Library 本地搜索范围文案断言。
- 不涉及 `library/query.py` 行为变更、后端 API 变更、数据迁移或外部依赖。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不新增排序、保存搜索、远程搜索或高级检索语法。
- [ ] Library detail 的正文预览和本地打开能力不在本变更内。
