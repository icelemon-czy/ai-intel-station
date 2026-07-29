# 输出归档

## 适用任务

- 调整 `output/` 目录结构
- 解释某份已抓取 Markdown 是由哪个工具生成的
- 判断哪些文件可手改、哪些应回到生成脚本修

## 目录职责

```text
output/
  ├─ wechat/   ← `research collect wechat` 生成（文章目录内追加 research-item.json）
  ├─ github/   ← `research collect github` 生成（repo 目录追加 research-item.json，search 目录追加 research-items.jsonl）
  ├─ papers/   ← `research collect papers` 生成（每篇 Markdown 旁追加 <stem>.research-item.json）
  ├─ briefing/ ← `research briefing` 生成（digest / reading-list 等派生阅读产物）
  └─ twitter/  ← 预留，当前无真实生成器
```

## 关键约束

- `output/` 默认是生成层，不是业务源码层
- 改目录命名或文件布局时，必须回到对应脚本修改默认输出目录和写文件逻辑
- `research backfill` 是现有历史产物 sidecar backfill 的统一入口；不要在 `output/` 下手工补 JSON 掩盖脚本缺陷
- `output/briefing/` 是派生阅读产物区，不应反向成为原始资料的唯一事实来源
- 样例内容可以保留作研究资料，但不要靠手工修补去掩盖生成器问题
- `twitter/` 目前是空占位；开始实现前先补 feature / rules / spec / validation 文档

## 生成器映射

| 输出目录 | 生成器 | 关键函数 |
| --- | --- | --- |
| `output/wechat/` | `research collect wechat` | `collect/wechat.py` + `research-item.json` |
| `output/github/` | `research collect github` | `collect/github.py` + `research-item*.json*` |
| `output/papers/` | `research collect papers` | `collect/papers.py` + `<stem>.research-item.json` |
| `output/briefing/` | `research briefing` | `write_digest_report()` / `write_reading_list_report()` |

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |
| 顶层来源目录名 | 所有脚本默认输出路径 + AGENTS / CLAUDE / `.compass/context` |
| 单来源文件布局 | 对应 feature README + 工具 README / SKILL |
| `output/briefing/` 子树规则 | `briefing/reports.py` + `publish/obsidian.py` + `.compass/context` 文档 |
| 样例文件清理 | 是否还有引用这些样例的文档或验证记录 |

## 排查思路

1. 先确定产物来自哪个工具。
2. 再回到该工具的 Markdown 组装函数，而不是先编辑输出文件。
3. 如果只有某一份历史输出异常，判断是旧版本产物还是脚本当前行为。
4. 若历史 Markdown 缺 sidecar，优先运行 `uv run research backfill output` 回填。
5. 若 briefing 内容异常，先确认 sidecar 与 query 结果是否正确，再看 `briefing/reports.py` 的展示逻辑。

