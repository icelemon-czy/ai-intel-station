# 简报生成

## 适用任务

- 改 daily signal / digest / reading list 的 Markdown 结构
- 调整 Obsidian 友好的输出路径或 slug 规则
- 排查部分成功时为什么没有写出缺失来源

## 入口与关键文件

- `research/cli.py` — `briefing` 的统一入口
- `briefing/reports.py` — digest / reading list Markdown 生成
- `briefing/signals.py` — daily freshness、dedupe、corroboration、ranking、confidence 与 outcome
- `research/discovery/runner.py` — selected source coverage 与 signal briefing orchestration
- `publish/obsidian.py` — `output/briefing/` 路径规则与写文件辅助
- `library/query.py` — briefing 的上游筛选输入
- `tests/test_restructure_research_architecture.py` — digest / reading-list / missing-source 验证

## 主数据流

```text
research briefing <mode> <keyword>
  → research/cli.py
  → query_research_items(output_root, ...)
  → build_digest_markdown() or build_reading_list_markdown()
  → _coverage_note() 写缺失来源
  → briefing_output_path()
  → output/briefing/digests/ or output/briefing/reading-lists/

research discover
  → local ResearchItem(signal + evidence)
  → lane-specific source-time freshness gate
  → papers > github > news exact dedupe + corroboration + deterministic rank
  → output/briefing/signals/ + structured status
```

## 关键约束

- briefing 是派生阅读层，不允许覆盖 `output/github` / `output/papers` / `output/wechat`
- 第一阶段至少支持 `digest` 和 `reading-list` 两类产物
- daily default 是 5 条 News（至少 2 条 deduped WeChat）+ 1 GitHub + 1 arXiv；
  GitHub/Papers 保持 evidence role，只 MAY 在 dedicated lane 成为 primary item
- `ready|partial|no_fresh_signals|coverage_incomplete` 是可消费的 daily outcome；`failed|dry_run|legacy` 不得伪装成今日结果
- 若只收集到部分来源，仍要生成 Markdown，并明确写出 `Missing sources: ...`
- 标题 slug 变化会影响 Obsidian 链接和历史文件路径，改前先检查输出兼容性

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |
| 调整 digest 样式 | `build_digest_markdown()` + traceability |
| 调整 reading list 样式 | `build_reading_list_markdown()` + Obsidian 查看习惯 |
| 改输出目录规则 | `publish/obsidian.py` + `features/archive-output/README.md` |
| 改 CLI 参数 | `research/cli.py` + overview / key-files / roadmap |
| 改 daily ranking / outcome | `briefing/signals.py` + signal-discovery/daily Specs + Skill + Web status + fixture tests |

## 验证

```bash
uv run --with pytest python -m pytest tests/test_restructure_research_architecture.py
uv run research briefing digest agent --source github --source papers
uv run --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_briefing_marker.py
```

## 已知边界

- WeChat account discovery 依赖 best-effort public index；failure 会降低 coverage，不会被解释为空结果
- fuzzy semantic dedupe 不在 deterministic layer；当前只合并 normalized URL 或 exact normalized title
