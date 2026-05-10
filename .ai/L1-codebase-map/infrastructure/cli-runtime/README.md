# CLI 运行时

## 这个组件解决什么问题

统一说明这个仓库里“命令应该从哪跑、真实入口在哪、依赖声明放哪”。当前它已经是一个统一打包的 workspace CLI，而不是多个并列来源脚本入口。

## 真实入口约定

| 工具 | 推荐运行方式 | 真实入口 | 备注 |
|------|--------------|----------|------|
| collect github | `uv run research collect github owner/repo` | `research/cli.py` → `collect/github.py` | `--search` 合并到同一子命令 |
| collect papers | `uv run research collect papers cs.AI --max 10` | `research/cli.py` → `collect/papers.py` | `--list` 合并到同一子命令 |
| collect wechat | `uv run research collect wechat "<url>"` | `research/cli.py` → `collect/wechat.py` | 统一从根目录运行 |
| query | `uv run research query agent --source github` | `research/cli.py` → `library/query.py` | 本地 sidecar-only |
| briefing | `uv run research briefing digest agent` | `research/cli.py` → `briefing/reports.py` | 只写 `output/briefing/` |
| backfill | `uv run research backfill output` | `research/cli.py` → `library/items.py` | 历史 Markdown sidecar 回填 |

## 运行时边界

- 根目录 `pyproject.toml` 维护统一依赖和 `research` console script
- `collect/`、`library/`、`briefing/`、`publish/` 是运行时核心层；来源目录不再是 runtime source of truth
- 改动时先判断是 operator surface 变化，还是某个 collect 子命令的业务行为变化

## 修改时优先级

1. 先确认用户实际执行的是哪条 `research ...` 命令。
2. 再确认变化落在 `research/cli.py` dispatch，还是落在 `collect/` / `library/` / `briefing/` 内部。
3. 新依赖默认加到根级 `pyproject.toml`，除非明确只是历史资料目录用途。
4. 如果改子命令语义，要同步 README / SKILL / `.ai`。

## 相关文件

- `pyproject.toml`
- `research/cli.py`
- `AGENTS.md`
- `CLAUDE.md`