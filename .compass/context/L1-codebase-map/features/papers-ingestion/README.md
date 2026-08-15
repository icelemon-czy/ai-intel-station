# arXiv 论文抓取

## 适用任务

- 调整 arXiv 类别白名单
- 改论文 Markdown 摘要格式或文件命名
- 排查 API 返回、XML 解析、类别过滤或落盘问题

## 入口与关键文件

- `research/cli.py` — 统一运行入口，负责 dispatch 到 papers collect 动作
- `collect/papers.py` — papers 收集的真实实现
- `tools/papers/SKILL.md` — 来源参考资料，可作为 papers collect 能力说明参考
- `output/papers/` — 论文归档输出目录

## 主数据流

```text
research collect papers ...
  → research/cli.py dispatch
  ├─ --list
  │   → 打印 AI_CATEGORIES 说明并退出
  └─ categories 模式
      → fetch_papers_by_category()
      → arXiv search API（bounded retry）
      → official category Atom feed fallback（429 / timeout / 5xx）
      → 解析 Atom XML
      → paper_to_markdown()
      → build_paper_item()
      → save_papers()
      → output/papers/arXiv-<category>/NN-title.md + NN-title.research-item.json
```

## 关键约束

- 只支持 `AI_CATEGORIES` 中列出的类别；未知类别当前只 warning，不抛异常
- 数据源是 arXiv 公共 search API；遇到 throttle 或 transient failure 时回退到官方 daily
  category Atom feed。两者都无认证，但网络和返回格式变化会直接影响解析
- 每次 search API request 最多尝试两次、单次 15 秒；fallback 只尝试一次，避免 daily run
  因单个 category 无限阻塞
- 每个 category 单独落到 `arXiv-<category>/`，每篇文件名前缀用两位编号
- 文件名安全化逻辑在 `save_papers()`，改它会影响整个目录的稳定性
- papers sidecar 文件名和 Markdown stem 绑定；改命名规则时要同步 backfill 与历史样本兼容性

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |

| 改类别白名单 | `AI_CATEGORIES` + `SKILL.md` + L3 spec |
| 改论文摘要模板 | `paper_to_markdown()` + 现有 output 样本 |
| 改文件命名 | `save_papers()` + 目录可重放性 |
| 改 `--list` / `--max` 语义 | `main()` 参数说明 + `.compass/context` 文档 |

## 验证

```bash
uv run research collect papers --list
uv run research collect papers cs.AI --max 3
uv run python -m pytest -q tests/test_papers_atom_parse.py tests/test_save_papers.py
```

## 已知边界

- parser、transport/fallback 与 Markdown/sidecar 有 deterministic test；真实 availability 仍需
  `research collect papers cs.AI --max 1` smoke run 验证
- 一个类别失败时脚本会继续跑其他类别，排查时不要误以为全局成功
