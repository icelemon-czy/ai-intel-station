# GitHub 仓库研究

## 适用任务

- 拉取单个仓库的 Markdown 摘要
- 调整 GitHub 搜索输出格式
- 排查 `gh` 认证、repo 查询、issue 列表或输出目录问题

## 入口与关键文件

- `research/cli.py` — 统一运行入口，负责 dispatch 到 GitHub collect 动作
- `collect/github.py` — GitHub 收集的真实实现
- `tools/github/SKILL.md` — 来源参考资料，可作为 GitHub collect 能力说明参考
- `output/github/` — repo 快照和搜索结果落盘位置

## 主数据流

```text
research collect github ...
  → research/cli.py dispatch
  ├─ --search
  │   → gh search repos
  │   → 组装 search.md
  │   → build_github_search_items()
  │   → output/github/<query>/search.md + research-items.jsonl
  └─ repo 模式
      → run_gh()
      → fetch_repo()
      → repo_to_markdown()
      → build_github_repo_item()
      → save_repo()
      → output/github/<owner-repo>/README.md + research-item.json
```

## 关键约束

- 依赖本地 `gh` CLI；没有安装或未登录时会在 `run_gh()` 处失败
- repo 模式当前会抓取仓库元数据和最多 20 条 open issues
- `--issues` 参数已声明，但当前实现中 repo 模式本来就会抓 issue；改这个行为前先确认想保留还是修正
- 输出目录按 `<owner>-<repo>` 和 `<query>` 命名，改名会影响历史归档和文档示例
- GitHub 目录下现在同时承载 Markdown 和 normalized sidecar；如果要改 sidecar 文件名，需同步 backfill 解析逻辑

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |

| 改 repo Markdown 模板 | `repo_to_markdown()` + 历史输出样例 |
| 改 search 结果格式 | `main()` 的 `--search` 分支 + `search.md` 约定 |
| 改 issue 采集逻辑 | `fetch_repo()` + `--issues` 语义说明 |
| 改输出目录规则 | `output/github/` + `SKILL.md` + `.ai` 文档 |

## 验证

```bash
gh auth status
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
```

## 已知边界

- 当前没有自动化测试；修改后至少做命令级 smoke run
- 真实数据来自 `gh`，不是本仓库内的 GitHub SDK 或 HTTP client
