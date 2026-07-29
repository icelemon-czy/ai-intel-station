# Fix Web Contract Probe HTTP Methods

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

- `2026-07-29 23:29` — [无] → [drafting] by /fix-bug | 原因: release gate 真实复现 contract probe 用 GET 请求 POST endpoint 并错误报告 backend 缺 route
- `2026-07-29 23:29` — [drafting] → [implementing] by /fix-bug | 原因: main Web Spec 无业务歧义；根因是 test oracle 未建模 HTTP method 与 valid request input
- `2026-07-29 23:34` — [implementing] → [pending-review] by /fix-bug | 原因: method-aware contract 与相邻 real full-stack tests 全绿，temporary output isolation 已验证
- `2026-07-29 23:38` — [pending-review] → [approved] by /fix-bug | 原因: Main Agent fallback review PASS；bundle coverage、HTTP method、dynamic input、intentional error 与 no-remote isolation 均闭合
- `2026-07-29 23:38` — [approved] → [archived] by /fix-bug | 原因: main Spec 无 delta 待合并；L5 traceability 与 report 已更新，归档完成

## Why

`web/test/fullstack.contract.test.mjs` 从 built frontend 提取 API path 后统一发送 GET。
`/api/briefing/preview`、`/api/briefing/save`、`/api/collect/run` 与
`/api/discover/run` 实际由 frontend 以 POST 调用，因此 test 把正确 backend behavior
误报为 404。dynamic GET routes 还需要 query parameter，单纯 strip query 同样可能产生
false failure。

## What Changes

- 为每个 frontend API literal 建立 method-aware contract descriptor。
- 保留 built bundle path coverage，新增 path → contract 一一对应检查，防止漏测新增 endpoint。
- 在 isolated temporary output root 构造最小真实 sidecar，使 detail、preview 与 save probe
  不读写 repository archive。
- 对需要 intentional 4xx 的 unknown job 使用 route-specific response assertion，
  区分已命中 route 与 unknown API path。

## Alternatives Considered

1. **允许任何 4xx** — 仍无法区分 method/path 不存在与 input error。
2. **继续只测 GET path existence** — 无法验证 frontend 实际 request contract。
3. **把 API registry 加进 production runtime** — 会为 test 引入新的 abstraction，
   与当前轻量 Agent-first方向不符。
4. **test-local descriptor + bundle coverage（当前选择）** — 用最小 test oracle 建模
   method、valid input 与 expected response，同时继续自动发现新增 frontend path。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- 无 Spec 变更；修复 `web-workspace` 的 full-stack validation defect。

## Impact

- Tests: `web/test/fullstack.contract.test.mjs`
- Validation: Web traceability、test-spec 与 release report
- Runtime: 无 product code change

## Review Feedback

- 无。

## Known Gaps

- 无。
