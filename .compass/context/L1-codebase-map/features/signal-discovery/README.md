# Realtime Signal Discovery

## 目标

回答“今天有什么值得看”时，用 realtime source 组成 News lane，并从 fresh GitHub / Papers
evidence 组成 dedicated lane。不把 lifetime popularity 或无 source time 的条目包装成今日趋势。

```text
HN / WeChat watchlist / optional X
  → ResearchItem(signal)
  → publication-time gate (default 48h, max 72h)
  → News rank + reserve deduped WeChat minimum
  → papers > github > news exact dedupe + corroboration
  → 5 News (2 WeChat min) + 1 GitHub + 1 arXiv
  → output/briefing/signals/ + source coverage status

GitHub / Papers → ResearchItem(evidence) → lane-specific source-time gate ─┘
```

## 入口与关键文件

- `research/discovery/runner.py` — source fault isolation 与 coverage 传递
- `collect/hackernews.py` / `collect/x.py` / `collect/wechat_index.py` — bounded adapter
- `library/items.py` — `discovered_at` / `signal_role` / `discovery_method`
- `briefing/signals.py` — freshness、dedupe、corroboration、ranking、status 与 Markdown
- `tests/test_realtime_signals.py` — fixture source + deterministic contract

## 核心约束

- News item 必须由 `signal` 发起，且 `published_at` 可解析并在 freshness window 内。
- `discovered_at` 是第一次观测时间，重复收集不得刷新，也不得代替 publication time。
- GitHub repository/search 和 Papers 保持 `evidence`；不能填充 News，但 fresh item 可进入 dedicated lane。
- WeChat minimum 按 deduped rendered News entry 计数；shortfall 必须保持 `partial`，不能用 HN/X 冒充。
- 跨平台 engagement 不比 raw count，只比同 source candidate percentile。
- 每次 run 的 status 是 `ready|partial|no_fresh_signals|coverage_incomplete`；
  `failed|dry_run|legacy` 不是可当作今日 signal result 的状态。
- WeChat public index 是 best effort；CAPTCHA、空页、解析失败或缺 publication time
  必须算 coverage failure。

## 验证

```bash
uv run --extra dev python -m pytest -q tests/test_realtime_signals.py
uv run research discover --dry-run --source hackernews,wechat
```
