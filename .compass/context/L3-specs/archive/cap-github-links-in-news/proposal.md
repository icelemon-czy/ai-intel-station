# Cap GitHub Links in News

> **状态**: archived
> **创建**: 2026-08-15
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

## Status Machine（不要删）

```text
drafting → implementing → pending-review → approved → archived
                 ↑              │
                 └ review-failed┘
```

| 状态 | 含义 | 由谁推进 |
|:-----|:-----|:---------|
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 +代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项，记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 转移日志（append-only）

- `2026-08-15 14:21` — [无] → drafting by /develop | 原因: daily News 5 条中 4 条指向 GitHub，用户确认实施 review 建议
- `2026-08-15 14:35` — drafting → implementing by /develop | 原因: plan review PASS；composition、migration、dual-cap、status、attribution 与 test surface 无 blocker
- `2026-08-15 14:44` — implementing → pending-review by /develop | 原因: 116 targeted/core tests + 4 subtests 通过；local 7-item briefing 的 News GitHub destination 为 1/1
- `2026-08-15 14:51` — pending-review → review-failed by sdd-reviewer | 原因: 缺 non-default YAML production-path assertion；L1 flow 的 dedupe/cap 顺序写反
- `2026-08-15 14:51` — review-failed → implementing by /develop | 原因: reviewer blocker 可由 deterministic test 与 doc correction 直接修复
- `2026-08-15 14:54` — implementing → pending-review by /develop | 原因: non-default YAML 已贯穿 production runner assertion；L1 flow 已改为 cross-lane dedupe 后 apply caps；117 tests + 4 subtests 通过
- `2026-08-15 15:01` — pending-review → approved by sdd-reviewer | 原因: verify PASS；delta scenarios、production implementation、meaningful assertions 与 evidence 完整
- `2026-08-15 15:03` — approved → archived by /develop | 原因: delta 已合并到 main Specs，L1/L2/L5 已同步

## Why

当前 News lane 按 discovery source role 分类；HN story 即使指向 GitHub repository 也可填满
News quota。X disabled、WeChat unavailable 时，default briefing 因而可能展示 1 条 dedicated
GitHub 加 4 条 GitHub-linked News，数量完整但内容结构失真。Renderer 同时把
`[hackernews]` attribution 链接到 story target，而不是已保存的 HN discussion。

## What Changes

- quota-mode briefing 新增 `github_news_max_items`，default 为 1，范围为 `0..news_items`。
- 在 cross-lane dedupe 后，按 deduped rendered News entry 的 normalized destination host 应用 cap；
  `github.com` 及其 subdomain 计入，`*.github.io` 不计入。
- 超过 cap 的 candidate 用后续 eligible non-GitHub candidate 补位；补不到时保留 News shortfall。
- legacy `max_items` mode 不启用新 cap，保持兼容。
- existing quota config 缺少 field 时迁移为 default 1；`max_items + github_news_max_items`
  作为 mixed legacy/quota config 拒绝；digest/reading-list ignore 该 field。
- maximum 不要求 GitHub collector enabled 或进入 `briefing.sources`，也不形成 required source
  coverage；它只约束 News destination composition。
- mixed WeChat/GitHub entry 同时消耗两个 slot；GitHub maximum 优先，不能被 positive WeChat
  reservation 绕过。冲突产生 WeChat minimum/News shortfall。
- `github_news_max_items=0` 且只有 fresh GitHub-target signal 时 outcome 保持
  `no_fresh_signals`，artifact 明示 candidates 被 composition cap 排除，不能声称没有 fresh input。
- quota artifact 展示 GitHub destinations actual/maximum 与 excluded candidate count。Excluded
  精确定义为 post-cross-lane-dedupe greedy selection 为填 News quota 实际遇到、且仅因 GitHub
  maximum 跳过的 deduped entry；dedicated corroboration duplicate 与 selector 已填满后未访问的
  lower-ranked candidate 不计。
- dry-run 只展示 configured maximum；actual/excluded 明示 unavailable，不伪装成执行结果。
- HN contribution attribution 使用 `metadata.discussion_url`，entry title 仍链接 saved canonical
  target（normalized URL 只用于 identity/host classification）；
  historical item 缺 discussion URL 时 fallback canonical target。

## Alternatives Considered

1. **只移除 `showstories`** — 可减少 repo launch，但 `newstories` 同样包含 GitHub target，不能修复分类边界。
2. **把 News 重命名为 Realtime Signals** — 描述现状但不解决用户需要的内容多样性。
3. **按所有 destination domain 做统一 cap** — 规则过宽，会无依据限制重要 editorial domain。
4. **GitHub destination 单独 configurable cap（当前选择）** — 直接修复已观察问题，保留一条高价值 HN repo launch，并能诚实报告 replacement 不足。

## Capabilities Affected

### Modified Capabilities

- `signal-discovery`: News selection 增加 GitHub destination cap 与 replacement/shortfall contract。
- `briefing`: source attribution 区分 HN discussion 与 original target。

## Impact

- Config/runtime: `research/discovery/config.py`, `runner.py`, example/personal config
- Selection/rendering: `briefing/signals.py`
- Tests: `tests/test_realtime_signals.py`, `tests/test_discovery_config.py`, runner assertions
- Docs/Skill: daily composition 和 signal-discovery context

## Review Feedback

- [x] 2026-08-15 plan review: 补齐 main Spec reconciliation、legacy migration、host decision
  table、WeChat dual-cap、cap=0 copy/status 与 raw target link contract → resolved in drafting。
- [x] 2026-08-15 plan re-review: 拆分 dual-cap replacement、明确 cap=0 total-entry 前提并定义
  exact excluded count → resolved in drafting。
- [x] 2026-08-15 final plan review: 补 non-HN attribution assertion 与 renderer
  actual/max/excluded、dry-run unavailable verification → resolved in drafting。

## Known Gaps

- destination kind 目前只解决 explicit GitHub host；其他 project homepage 的 semantic
  classification 不在本 change 范围。
