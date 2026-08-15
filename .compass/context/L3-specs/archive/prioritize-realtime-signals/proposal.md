# Prioritize Realtime Signals

> **状态**: archived
> **创建**: 2026-08-13
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
| review-failed | implementing | /develop 或 /fix-bug（开始修复 finding 或落实已确认决策）|
| pending-review | approved | /develop（SDD review PASS）|
| approved | archived | /develop（自动合并并验证）|

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-08-13 22:26` — [无] → [drafting] by /develop | 原因: user 确认以 realtime signal 为每日情报主线，要求先更新 docs 再按文档实现
- `2026-08-13 22:46` — [drafting] → [implementing] by /develop | 原因: 两轮 sdd-reviewer plan finding 已全部落实；source ownership、status/coverage、evidence role、success/failure、compatibility 与 deterministic ranking contract 已闭合，文档结构测试 11/11 通过
- `2026-08-13 22:59` — [implementing] → [pending-review] by /develop | 原因: realtime collector、signal model、ranking/briefing、status/coverage、CLI/config 与 Agent contract 已实现；targeted 62/62、core 418/418、runner 15/15 与 optional WeChat 16/16 通过
- `2026-08-13 23:07` — [pending-review] → [review-failed] by /develop | 原因: verify review 发现 Web status parser 不识别带 status 的新 marker，且 X request 缺少由 freshness config 约束的 start/end time
- `2026-08-13 23:07` — [review-failed] → [implementing] by /develop | 原因: 开始修复两个 blocking finding 并补 Web/X boundary regression tests
- `2026-08-13 23:09` — [implementing] → [pending-review] by /develop | 原因: Web marker/status 及 X start/end freshness range 已修复；blocker-targeted 52/52、core 426/426 和 runner 15/15 通过
- `2026-08-13 23:16` — [pending-review] → [review-failed] by /develop | 原因: re-review 发现 Web UI 丢弃 briefing status，导致 no_fresh_signals 与 coverage_incomplete 都只显示为 0 items
- `2026-08-13 23:16` — [review-failed] → [implementing] by /develop | 原因: 开始补 Web outcome copy、两条展示路径与 frontend regression tests
- `2026-08-13 23:18` — [implementing] → [pending-review] by /develop | 原因: Web 两条 outcome 展示路径已修复并区分 honest empty / incomplete coverage；frontend 102/102 通过（2 个 loopback skip），production build 成功
- `2026-08-13 23:19` — [pending-review] → [approved] by /develop | 原因: sdd-reviewer final verify PASS；Spec、implementation、compatibility、security 与 anti-overfit test 无剩余 blocker
- `2026-08-13 23:25` — [approved] → [archived] by /develop | 原因: delta Requirements 已合并到 main Specs；README、AGENTS、L1/L2/L5 与 traceability 已同步，context structure tests 11/11 通过

## Why

当前 daily discovery 把按 lifetime stars 排序的 GitHub repository search 和 arXiv category
更新当作“今天值得看”的主要输入；WeChat 只会重复抓取预先提供的 article URL，系统没有
social discovery、first-observed time、source role、跨来源 corroboration 或 freshness-first
ranking。结果可以成功归档资料，却不能可靠回答“今天正在发生什么”。

## What Changes

- 新增 discovery-only realtime signal source：无需认证的 Hacker News feed，以及显式配置
  credential 后才运行的 X recent search；两者通过 `research discover --source` 使用，不新增
  standalone `research collect` 子命令。
- 将 WeChat 从纯 article URL fetch 扩展为 account watchlist 的 best-effort public-index discovery；
  CAPTCHA、空索引或无法解析 MUST 显式成为 coverage failure，不得伪装成“今天没有内容”。
- 扩展 ResearchItem，记录 `discovered_at`、`signal_role` 与 `discovery_method`；旧 sidecar
  保持可加载，backfill 不得把历史资料伪装成今日发现。
- 新增 daily signal briefing：只有具有可信 publication timestamp 且位于 configured freshness
  window 的 signal 可以发起 Top item；GitHub snapshot 和 Papers 默认只作为 evidence。
- daily signal briefing 最多输出 5 条，执行 deterministic dedupe、watchlist/freshness/
  corroboration ranking，并为每条展示“是什么”“为什么现在值得看”、source/time、evidence 和 confidence。
- 没有 fresh signal 且本次 selected + enabled realtime source coverage 完整时生成显式
  `no_fresh_signals` artifact；coverage 不完整时生成 `coverage_incomplete`，不得用旧
  GitHub/Papers 填充或把失败解释为安静的一天。
- GitHub repository/search 与 Papers 默认标记为 evidence；直接 WeChat article URL 与 WeChat
  watchlist、Hacker News、X 标记为 signal，但仍必须通过真实 publication-time gate。
- GitHub repository search 改为 recency-oriented metadata 和 ordering，避免 lifetime stars
  被误解为今日 trend；search artifact 写入必须返回真实 Path，不能污染 run report。
- source failure 保持 fault isolation；briefing 和 run log 显示每个 configured source 的
  succeeded / skipped / failed 与 coverage limitation。

## Alternatives Considered

1. **只启用固定 WeChat URL** — 实现最小，但只能重复归档已知文章，没有 discovery value。
2. **完全依赖 desktop browser automation** — 能复用登录态，但 CAPTCHA、安全策略与无人值守
   schedule 使其不适合作为 deterministic runtime；仅保留为 interactive recovery，不进入主链路。
3. **只做 broad topic search** — 覆盖广，但早期噪声和跨平台 engagement 不可比，会再次产生
   “看起来很多、真正有用很少”的结果。
4. **Watchlist-first signal + evidence（当前选择）** — 先保证用户关心来源的 freshness，
   再用 HN/X topic discovery 扩展覆盖，用 GitHub/Papers 验证，不新增 database 或 opaque model score。

## Capabilities Affected

### New Capabilities

- `signal-discovery`: 收集、标准化并排序 realtime social signal。

### Modified Capabilities

- `collection`: daily discovery 增加 Hacker News 与 X source，standalone collect surface 不变。
- `research-operations`: Hacker News 与 X 只扩展 discover source selector，不新增 standalone collect command。
- `daily-discovery`: daily run 以 signal briefing 和显式 coverage status 为主。
- `library`: ResearchItem 增加 observation 与 source-role metadata。
- `briefing`: 新增 freshness-gated Top signals artifact。
- `wechat`: 新增 account watchlist 的 best-effort discovery。
- `github`: repository snapshot/search 统一作为 evidence，search 从 lifetime popularity 改为 recency ordering。
- `papers`: Papers 统一作为 supporting evidence，不独立发起 daily Top item。

## Impact

- Config / CLI: `research/discovery/config.py`、`research/cli.py`、example 与 personal config；
  HN/X 仅扩展 discover source selector，不扩展 standalone collect command
- Collect: `collect/hackernews.py`、`collect/x.py`、`collect/wechat_index.py`、`collect/github.py`
- Model / query: `library/items.py`、`library/query.py`
- Ranking / render: `briefing/signals.py`、`research/discovery/runner.py`、run log status
- Agent contract: `.agents/skills/daily-discovery/SKILL.md`
- Tests: source fixtures、config validation、sidecar compatibility、freshness/dedupe/ranking、partial coverage、CLI dispatch
- Docs/context: README、AGENTS、L1/L2/L5 与主 Specs 在 closeout 同步

## Review Feedback

<!-- plan / verify review findings append here -->

- Verify round 1: BLOCKED — `workspace_web/service.py` 只解析 legacy briefing marker，无法向 Web status 暴露 signal outcome。
- Verify round 1: BLOCKED — X recent-search 只有 result limit，未传 `start_time/end_time`，与 configured freshness range contract 不一致。
- Verify round 2: BLOCKED — Web latest-status 与 completed-job UI 未展示 structured briefing status，用户无法区分完整覆盖下的安静日和 coverage failure。
- Verify round 3: PASS — Web 两条路径均展示 structured outcome，真实 SSR component tests 区分 `no_fresh_signals` 与 `coverage_incomplete`；无剩余 blocker。

## Known Gaps

- [ ] WeChat arbitrary-account discovery depends on a public index and remains best-effort; official-account-owned APIs or a user-provided feed MAY be added as another adapter later without changing the signal contract.
- [ ] Reddit is not included in this change because its current official developer surface is app/community scoped; the source-provider boundary leaves room for a later connector.
