# Fix arXiv API Transport

> **状态**: archived
> **创建**: 2026-08-15
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
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项，记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 转移日志（append-only）

- `2026-08-15 09:31` — [无] → drafting by /fix-bug | 原因: user 报告 daily arXiv collection 全部失败
- `2026-08-15 09:31` — drafting → implementing by /fix-bug | 原因: main Papers Spec 已明确 Fetch one category contract；根因是 code 使用非官方 HTTPS transport，无业务歧义
- `2026-08-15 09:51` — implementing → pending-review by /fix-bug | 原因: regression、live one-paper smoke、Papers-only discovery 与 scoped core regression 已完成
- `2026-08-15 09:58` — pending-review → review-failed by sdd-reviewer | 原因: 缺少 5xx retry exhaustion → official feed 的 deterministic anti-overfit assertion
- `2026-08-15 09:58` — review-failed → implementing by /fix-bug | 原因: 补 exact URL sequence、bounded sleep 与 successful fallback regression
- `2026-08-15 10:00` — implementing → pending-review by /fix-bug | 原因: 5xx exhaustion anti-overfit test 16/16 通过，scoped diff check 通过
- `2026-08-15 10:02` — note by /fix-bug | 修正 09:31 原因描述：`export.arxiv.org` 是 official search API；实际 defect 是 urllib timeout / shared throttle 下缺少 bounded resilience
- `2026-08-15 10:02` — pending-review → approved by sdd-reviewer | 原因: re-review PASS；transport、fallback、metadata、isolation 与 L5 evidence 无 blocking finding
- `2026-08-15 10:02` — approved → archived by /fix-bug | 原因: main Spec 无需变更，L1/L5 sync 完成，自动归档

## Why

`collect/papers.py` 请求 `https://export.arxiv.org/api/query`。受限环境报 DNS failure；获准的
非沙箱 `urllib` 请求能解析 host，但 search API 在 read timeout 后又返回 HTTP 429；同一 query
通过 `curl` 可返回，说明不是 category/query 错误，而是当前 Python transport 与共享 API throttle
组合下不可靠。`Connection: close` 能改善部分请求，但不能独自覆盖 timeout/429。结果是 Papers
lane 无法稳定收集今日 arXiv evidence。

## What Changes

- 保留 arXiv HTTPS query endpoint，并为 one-shot request 显式发送 `Connection: close`。
- 新增 network-boundary regression，验证 category query 的 HTTPS endpoint 与 close semantics。
- 对 transient timeout/5xx 增加一次 bounded retry；429 或 retry exhaustion 使用 arXiv 官方
  category Atom feed fallback，并继续遵守 `max_results`。
- 兼容 official category feed 的 `dc:creator`，并从 canonical abstract link 恢复 arXiv id/PDF link。
- 跑 parser/runner regression 与真实 one-paper smoke，再执行 Papers-only discovery。

## Capabilities Affected

### Modified Capabilities

- 无 Spec 变更；恢复 existing `papers` Latest Papers by Category contract。

## Impact

- Runtime: `collect/papers.py`
- Tests: `tests/test_papers_atom_parse.py`
- Validation: Papers traceability 与 fix report

## Out of Scope

- Direct `research collect papers` 的 remote failure exit-code 语义是独立 operator-surface bug，
  不与本次 transport 修复混合。

## Review Feedback

- 首轮 verify `BLOCKED`：实现虽覆盖 5xx classification 与 retry exhaustion fallback，但 tests
  只有 timeout retry 和 immediate 429 fallback，无法防止 5xx 不重试或第三次仍请求 search API
  的 regression。补充 `503 → 502 → official feed` exact sequence assertion 后重新 review。
- re-review `PASS`：新增 test 调用 production path，精确覆盖两次 search、第三次 official feed、
  retry-delay cap 与 successful parse；无剩余 blocking finding。

## Known Gaps

- 广域 pytest 当前会把 `tests/test_discovery_runner.py` 的 unittest-style module functions 当成
  pytest tests，产生 15 个缺 `self` fixture 的 collection error；同一文件经 `unittest` 15/15
  通过。该既有 test-runner wiring 问题不属于 arXiv transport 修复。
- 当前 shell 没有 `npm`，Web process test 无法执行；本 change 未改 Web source。
