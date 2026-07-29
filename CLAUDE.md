# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

AI Intel Station（AI 情报站）— 本地优先的 AI 研究工作区。负责收集 AI 领域内容，整理为统一资料库，并生成适合 Obsidian 阅读的简报。

## Business Architecture

```text
ai-intel-station/
├── research/        # 统一 operator surface（collect / query / briefing / backfill）
├── collect/         # 按来源收集原始资料
├── library/         # 统一 ResearchItem、sidecar、查询
├── briefing/        # digest / reading list 生成
├── publish/         # Obsidian 友好的输出路径与写文件
├── output/
│   ├── github/      # GitHub 原始归档
│   ├── papers/      # arXiv 原始归档
│   ├── wechat/      # WeChat 原始归档
│   └── briefing/    # 派生阅读产物
├── tests/           # 根级测试，围绕业务层和 operator surface
└── .agents/skills/ # canonical project Workflow + product Skill
```

## Skills

### Project Workflow Skills

Project Workflow 的唯一 source of truth 位于 `.agents/skills/<name>/SKILL.md`。

当用户明确调用或语义上命中这些 Workflow 时，完整读取对应 canonical Skill：

- `/init-project`, `/build-context`, `/brainstorm`, `/develop`
- `/fix-bug`, `/ask-codebase`, `/audit-tests`
- `/ralph-loop`, `/skill-creator`

不要创建 platform-specific full mirror；`.claude/skills/` 只保留需要 platform discovery 的
thin adapter。

### Product Operator Skill

Daily use is Agent-first. For “今天有什么值得看”、每日情报、自动探索、status 或 schedule，
load `.claude/skills/daily-discovery/SKILL.md`; it forwards to the canonical project Workflow in
`.agents/skills/daily-discovery/SKILL.md`. The Agent executes the deterministic CLI and reads local
artifacts. Web is an optional viewer, not a prerequisite.

| Skill | 说明 | 触发关键词 |
| ----- | ---- | ---------- |
| **daily-discovery** | Agent 执行每日情报、读取 artifact 并返回重点 | `今天有什么值得看`、`每日情报`、`status`、`schedule` |
| **wechat** | 抓取单篇微信公众号文章 | `抓取这篇微信`、`公众号 URL` |
| **github** | 抓取单个 repo 或执行一次 repo search | `抓取这个 repo`、`搜一次仓库` |
| **papers** | 按 category 执行一次 arXiv 收集 | `抓取 cs.AI`、`拉取这批论文` |

## Key Commands

### 收集

```bash
uv sync --extra wechat
uv run research collect wechat "<url>"
```

```bash
uv run research collect github owner/repo
uv run research collect github "query" --search
uv run research collect papers cs.AI --max 10
```

### 查询与简报

```bash
uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output
```

### 每日自动探索（可选）

```bash
uv run research init-config                # 写入 config/discovery.yaml（来自 example 模板）
uv run research discover --dry-run         # 不联网，预览会跑什么
uv run research discover --source papers   # 仅跑一个 source
uv run research schedule launchd           # 打印 macOS launchd 安装命令
uv run research schedule cron              # 打印 crontab 片段
```

详见 [docs/daily-discovery.md](docs/daily-discovery.md)。

## Tech Stack

- Python 3.10+ with `uv` for dependency management
- Core runtime only requires PyYAML
- Optional `wechat` extra: Camoufox + BeautifulSoup + markdownify + httpx
- arXiv public API for paper fetching
