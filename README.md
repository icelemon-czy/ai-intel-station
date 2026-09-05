# AI Intel Station

AI Intel Station（AI 情报站）是一个 local-first AI 研究工作区。它把 remote source 收集为可检查的本地 archive，通过统一的 Library contract 支持查询，并生成适合 Obsidian 阅读的 briefing。日常操作以 project Agent 为主；`research` CLI 是唯一 deterministic runtime，Web workspace 只是 optional viewer。

```text
Agent / CLI / optional Web
           ↓
 collect or discover ──→ source archive + ResearchItem sidecar
                                      ↓
                              query / briefing
```

## Document map

| 文档 | 负责什么 | 何时读取 |
|:-----|:---------|:---------|
| [`doc/system_design.md`](doc/system_design.md) | architecture source of truth、layer ownership、dependency direction 与 repository map | 先理解项目结构或判断改动归属时 |
| [`doc/research_library_design.md`](doc/research_library_design.md) | source collection、`ResearchItem` sidecar、本地查询与历史 backfill | 修改 collector、Library contract 或 archive 时 |
| [`doc/daily_discovery_design.md`](doc/daily_discovery_design.md) | 每日 signal sweep、source role、quota、coverage、config 与 schedule | 运行或修改 Daily Discovery 时 |
| [`doc/briefing_design.md`](doc/briefing_design.md) | digest、reading list 与 daily signal briefing | 修改派生阅读产物时 |
| [`doc/web_workspace_design.md`](doc/web_workspace_design.md) | optional Web viewer、HTTP boundary 与 background job | 修改 Web workspace 时 |
| [`doc/validation_design.md`](doc/validation_design.md) | test layer、真实 boundary 与 release validation | 设计 test 或执行 release check 时 |

当前正在进行 source-tree 整理（把 Python source 收拢到 `src/ai_intel_station/`）；进行中的迁移清单见 [`doc/todo.md`](doc/todo.md)，完成后删除。

## Operator entry

安装 core runtime：

```bash
uv sync --frozen
```

日常情报可以直接对 project Agent 说“今天有什么值得看？”。查看全部 deterministic command：

```bash
uv run research --help
```

首次运行 Daily Discovery：

```bash
uv run research init-config
uv run research discover --dry-run
uv run research discover
uv run research organize
```

`research organize` 从 sidecar 重建 date/tag/duplicate catalog，不移动 primary archive。direct WeChat article collection 的 optional dependency、Web workspace 启动方式与其他 feature-specific command 分别记录在对应 design，不在 README 重复维护。
