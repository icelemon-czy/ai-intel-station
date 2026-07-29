# 简报生成

## 适用任务

- 改 digest / reading list 的 Markdown 结构
- 调整 Obsidian 友好的输出路径或 slug 规则
- 排查部分成功时为什么没有写出缺失来源

## 入口与关键文件

- `research/cli.py` — `briefing` 的统一入口
- `briefing/reports.py` — digest / reading list Markdown 生成
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
```

## 关键约束

- briefing 是派生阅读层，不允许覆盖 `output/github` / `output/papers` / `output/wechat`
- 第一阶段至少支持 `digest` 和 `reading-list` 两类产物
- 若只收集到部分来源，仍要生成 Markdown，并明确写出 `Missing sources: ...`
- 标题 slug 变化会影响 Obsidian 链接和历史文件路径，改前先检查输出兼容性

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |
| 调整 digest 样式 | `build_digest_markdown()` + traceability |
| 调整 reading list 样式 | `build_reading_list_markdown()` + Obsidian 查看习惯 |
| 改输出目录规则 | `publish/obsidian.py` + `features/archive-output/README.md` |
| 改 CLI 参数 | `research/cli.py` + overview / key-files / roadmap |

## 验证

```bash
uv run --with pytest python -m pytest tests/test_restructure_research_architecture.py
uv run research briefing digest agent --source github --source papers
```

## 已知边界

- 当前只输出本地 Markdown，不提供 Web/TUI
- 当前 coverage note 只提示缺失来源，不做更细粒度的数据质量解释
