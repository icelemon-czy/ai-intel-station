# Fix Library Legacy Datetime Query

> **状态**: archived
> **创建**: 2026-07-29
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
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 +代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项（技术问题或未解决的产品语义），记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /develop |
| drafting | implementing | /develop（必要业务决策完成 + plan review）|
| implementing | pending-review | /develop（相关测试全绿）|
| pending-review | review-failed | /develop（SDD review BLOCKED）|
| review-failed | implementing | /develop 或 /fix-bug（开始修复或落实已确认决策）|
| pending-review | approved | /develop（SDD review PASS）|
| approved | archived | /develop（自动合并并验证）|

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-07-29 23:19` — [无] → [drafting] by /fix-bug | 原因: release audit 复现 repository output 的 legacy datetime 使 Library query 崩溃
- `2026-07-29 23:19` — [drafting] → [implementing] by /fix-bug | 原因: main Library Spec 已明确要求 local query 与 resilient loading，无业务歧义；进入 test-gap repair
- `2026-07-29 23:24` — [implementing] → [pending-review] by /fix-bug | 原因: public query/service regression、repository output round-trip 与 real Web full-stack tests 全绿
- `2026-07-29 23:28` — [pending-review] → [approved] by /fix-bug | 原因: Main Agent fallback review PASS；implementation 保持 user filter error contract，public regression 覆盖 legacy、malformed 与 updated fallback
- `2026-07-29 23:28` — [approved] → [archived] by /fix-bug | 原因: main Spec 无 delta 待合并；L5 traceability 与 report 已更新，归档完成

## Why

现有 archive 包含 `2026-04-02 08:31` 等 minute-precision datetime。Library filter
在无 date filter 时允许 item 进入，但 sort key 再次严格解析并抛出 `ValueError`，
使整个 Web Library request 失败。

## What Changes

- 为 minute-precision legacy datetime 增加兼容解析。
- 统一 item-side datetime 的 safe parse，使 malformed optional metadata 不崩溃 query sort。
- 补真实 sidecar + public query/service regression，避免只测 private parser。

## Alternatives Considered

1. **遇到 legacy datetime 就 skip item** — 能避免 crash，但会隐藏仍可用的本地资料。
2. **只在 Web service catch exception** — 会让 CLI、briefing 等其他 query caller 继续失败。
3. **在 Library query boundary normalize + safe sort（当前选择）** — 修复 source of truth，
   同时保留 malformed item 的无 date-filter可见性。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- 无 Spec 变更；修复 existing `library` Local Query / Resilient Sidecar Loading contract。
- 无 Spec 变更；恢复 existing `web-workspace` Library Search and Inspection contract。

## Impact

- Runtime: `library/query.py`
- Tests: `tests/test_library_query_datetime.py`，必要时补 public Web service regression
- Validation: Library / Web traceability 与 release report

## Review Feedback

- 无。

## Known Gaps

- 无。
