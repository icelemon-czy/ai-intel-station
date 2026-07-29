# 本地资料查询

## 适用任务

- 改跨来源关键词检索逻辑
- 增加或调整来源过滤、时间过滤
- 排查 briefing 结果为什么多了 / 少了某些条目

## 入口与关键文件

- `research/cli.py` — `query` 和 `backfill` 的统一入口
- `library/storage.py` — 扫描 `output/` 下既有 `research-item.json` / `research-items.jsonl`
- `library/query.py` — 查询入口，负责关键词、来源、时间窗口过滤
- `library/items.py` — `ResearchItem` schema 与历史 backfill、parser / builder
- `tests/test_restructure_research_architecture.py` — 查询过滤和统一入口验证

## 主数据流

```text
research query <keyword>
  → research/cli.py
  → query_research_items(output_root, keyword, sources, since, until)
  → load_research_items(output_root)
  → 遍历 research-item.json / research-items.jsonl
  → 按 title / summary / tags / authors 做关键词匹配
  → 按 source 做来源过滤
  → 按 published_at / updated_at 做可选时间过滤
  → 返回排序后的 ResearchItem 列表
```

## 关键约束

- 查询层只能消费本地 sidecar，不能在这里重新抓 GitHub / arXiv / WeChat
- 时间过滤必须是可选项；不传 `since` / `until` 时应返回完整命中集
- 过滤条件变化时，要同时检查 briefing 结果是否受影响
- 若历史样例没有 sidecar，优先先跑 `uv run research backfill output`

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |
| 改关键词匹配字段 | `library/query.py` + `tests/test_restructure_research_architecture.py` |
| 改 sidecar 扫描规则 | `library/storage.py` + `features/archive-output/README.md` |
| 改时间字段优先级 | `ResearchItem` schema + briefing 排序 / coverage 结果 |

## 验证

```bash
uv run --with pytest python -m pytest tests/test_restructure_research_architecture.py
uv run research backfill output
uv run research query agent --source github
```

## 已知边界

- 目前只基于本地 sidecar 做轻量过滤，不做全文索引或向量检索
- 时间比较依赖 sidecar 里的字符串时间格式，来源格式不统一时要谨慎兼容
