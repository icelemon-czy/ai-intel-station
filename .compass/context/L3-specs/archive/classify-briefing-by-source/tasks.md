# Implementation Tasks

## 1. Tests

- [x] 1.1 Default quota 选择 3 HN + 最多 2 WeChat + 1 GitHub + 1 arXiv；HN 指向 github.com 仍进 Hacker News。
- [x] 1.2 仅 WeChat 超过 maximum 时 WeChat 截断，HN 不足则报告 Hacker News shortfall，不再有 News missing。
- [x] 1.3 跨 source exact duplicate：dedicated GitHub 拥有 entry，匹配 HN 只作 corroboration，另一 distinct HN 仍可进入 Hacker News。
- [x] 1.4 existing `news_items=5` + `wechat_max_items=2` 无 `hackernews_items` 时迁移为 HN=5；`github_news_max_items` 忽略。
- [x] 1.5 Artifact 分组为 arXiv / GitHub / Hacker News / WeChat；x_items=0 时不渲染 X；dry-run 只报 configured source maxima。
- [x] 1.6 Skill 合同断言按 source 分组，不再要求 News 或 GitHub destination excluded。

## 2. Selector and renderer

- [x] 2.1 `DailyBriefingSelection` 改为 per-source lists 与 expected/max；删除 destination predicate 与 excluded count。
- [x] 2.2 `select_daily_briefing` 按 papers > github > hackernews > wechat > x 拥有 exact duplicate，并独立填 source quota。
- [x] 2.3 Markdown / quota table / why-now 使用 source 名；保留 HN discussion attribution。

## 3. Config, runner, Skill

- [x] 3.1 解析 `hackernews_items` / `x_items`，迁移 `news_items`，忽略 `github_news_max_items`，校验 required source。
- [x] 3.2 runner 传递新 quota，dry-run composition 按 source 描述。
- [x] 3.3 更新 example YAML、daily Skill、operator docs。
