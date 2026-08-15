# Add Daily Source Quotas

> **状态**: archived
> **创建**: 2026-08-14
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

- `2026-08-14 22:14` — [无] → [drafting] by /develop | 原因: user 要求 daily briefing 固定包含至少 1 条 arXiv、1 条 GitHub 与 5 条 realtime news
- `2026-08-14 22:34` — [drafting] → [implementing] by /develop | 原因: 三轮 plan review 后 source/status、legacy migration 与 cross-lane dedupe contract 均已闭合并 PASS
- `2026-08-14 22:48` — [implementing] → [pending-review] by /develop | 原因: quota production path、legacy migration、Agent/docs 与 targeted/core/runner/WeChat/Web/structure gates 全部验证通过
- `2026-08-14 22:53` — [pending-review] → [review-failed] by /develop | 原因: verify 发现 explicit-empty source fallback、attempted failure scope、integer type 与四类 anti-overfit test 缺口
- `2026-08-14 22:53` — [review-failed] → [implementing] by /develop | 原因: 开始落实 reviewer 已明确的 production/test 修复
- `2026-08-14 22:56` — [implementing] → [pending-review] by /develop | 原因: 三个 production blocker 与四类 anti-overfit gaps 已修复，完整 gates 重新全绿
- `2026-08-14 22:58` — [pending-review] → [review-failed] by /develop | 原因: verify round 2 仅剩 GitHub timestamp fallback 与 Paper latest-publication anti-regression assertion 缺口
- `2026-08-14 22:58` — [review-failed] → [implementing] by /develop | 原因: 补 public selector 的 source-time/ranking boundary test
- `2026-08-14 22:58` — [implementing] → [pending-review] by /develop | 原因: GitHub fallback、Paper latest publication 与 stale-published/fresh-updated exclusion 已由 public selector test 锁定，83 targeted tests 通过
- `2026-08-14 22:59` — [pending-review] → [approved] by /develop | 原因: verify round 3 PASS，无 remaining blocking finding
- `2026-08-14 23:04` — [approved] → [archived] by /develop | 原因: delta 已合并 main Specs，L1/L2/L5 已同步，Requirement/Scenario structure gates 11 passed

## Why

当前 daily briefing 最多输出 5 条 realtime signal，GitHub 与 Papers 只在 exact match 时作为
evidence 出现。即使当天成功收集了 arXiv 和 GitHub，用户仍可能只看到 Hacker News；这不满足
“每日既看 research / project，也看 social news”的阅读结构。

## What Changes

- 将默认 daily composition 改为三个独立 lane：5 条 `news`、1 条 `github`、1 条 `papers`，
  默认总计 7 条；5 条 news 中要求至少 2 条来自 WeChat。
- `news` lane 继续只接受 WeChat / Hacker News / X 的 verified fresh signal；GitHub/Papers
  仍保持 `evidence` role，但允许各自在 dedicated lane 中成为 primary reading item。
- Papers lane 使用 `published_at` freshness；GitHub lane 优先使用 `updated_at`，fallback 到
  `published_at`，并优先真正新创建且仍在 freshness window 的 repository。
- quota 不得通过 stale、timestamp-unknown 或其他 lane item 填充。缺项时保留已有结果，明确
  输出 expected / actual / missing；有 item 但 quota 未满足时 outcome 为 `partial`。
- News selection 先保留最多 2 个 fresh WeChat minimum slot，再用所有剩余 ranked news
  （HN / X / WeChat）填满 5 条；WeChat 不足不得用 HN/X 冒充已满足微信 minimum。
- 新 config 使用 `news_items=5`、`wechat_min_items=2`、`github_items=1`、`paper_items=1`。
  Legacy signals YAML 若只含 `max_items`，继续保持等量 News、且 dedicated/WeChat quota 为 0；
  `max_items` 与任何新 quota field 混用时拒绝，避免 silent reinterpretation。
- Positive quota 对应的 source 必须在 `briefing.sources` 中 enabled 且有可执行 target；否则
  config validation 在 network 前失败。Selective `--source` 漏掉 required lane 时 artifact
  显式 coverage incomplete，不可能 `ready`。
- Exact normalized URL/title 跨 lane 只展示一次：GitHub/Paper dedicated lane 拥有 entry，matching
  News 只作 corroboration；如果没有其他 candidate，News 报 quota shortfall。
- GitHub 与 Paper 彼此 exact duplicate 时使用 `papers > github > news` ownership precedence；
  loser lane 选择下一 eligible candidate，否则报告 shortfall。
- Daily Agent 与文档从“最多 5 条”同步为默认最多 7 条，并按 arXiv / GitHub / News 分组返回。

## Alternatives Considered

1. **在现有 Top 5 中软性混排** — 总数不变，但无法保证三个来源类型都有位置，HN engagement
   仍可能挤掉 arXiv/GitHub。
2. **缺项时用 stale item 补足** — 看起来永远有 7 条，但再次把旧内容包装成今天，违背
   verified freshness 与 honest coverage。
3. **独立 lane + honest shortfall（当前选择）** — composition 可预测，source role 仍清晰；
   远端失败或当天确无 fresh item 时展示缺口，不伪造配额完成。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `briefing`: daily artifact 从单一 Top 5 改为 5 news（至少 2 WeChat）+ 1 GitHub + 1 arXiv 的 quota composition。
- `signal-discovery`: evidence role 可进入 dedicated research lane；三类 lane 使用各自 freshness/rank。
- `github`: GitHub evidence 可作为 dedicated GitHub lane primary entry，但不能填 News quota。
- `papers`: Paper evidence 可作为 dedicated arXiv lane primary entry，但不能填 News quota。
- `daily-discovery`: Agent 默认返回最多 7 条，并报告 quota shortfall。

## Impact

- Config: `research/discovery/config.py`、`config/discovery.yaml.example`、ignored personal config
- Selection/render: `briefing/signals.py`、`research/discovery/runner.py`
- Agent/Web contract: `.agents/skills/daily-discovery/SKILL.md`；Web 继续消费 item count/status，
  不需要新增 endpoint
- Tests: config migration/validation、lane freshness/rank、exact quota、shortfall status、runner/Skill
- Docs/context: README、daily discovery docs、L1/L2/L5 与 main Specs

## Review Feedback

<!-- plan / verify review findings append here -->

- Plan round 1: BLOCKED — 缺 GitHub/Papers delta；required-source matrix、cross-lane ownership、deduped WeChat count、quota migration/bounds 与 dedicated confidence contract 未闭合。
- Plan round 2: BLOCKED — legacy max-only cap/status、positive News selective coverage 与 GitHub↔Paper exact duplicate ownership 仍需明确。
- Plan round 3: PASS — legacy cap、selective News coverage 与 `papers > github > news` ownership 均已形成可测试 contract。
- Verify round 1: BLOCKED — explicit `sources: []` 被 default fallback；attempted non-briefing source failure 未计入 incomplete；float quota 被截断；shortfall/dedupe/duplicate/confidence anti-overfit assertions 不完整。
- Verify round 2: BLOCKED — production implementation 对齐，仅缺 GitHub `updated_at` fallback 与 Paper latest `published_at` 的 meaningful public-selector assertion。

## Known Gaps

- [ ] Dedicated GitHub lane 以 repository create/update freshness 排序，不实现 GitHub Trending 的私有/抓屏算法。
- [ ] Source quota 只保证 composition，不保证每个 lane 的 semantic diversity；跨 lane fuzzy dedupe 仍不进入 deterministic layer。
