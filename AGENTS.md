# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

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
└── .Codex/skills/  # 项目级 skill 配置
```

## Skills

### Project Workflow Skills

This project now keeps a Codex-specific workflow skill copy under `.Codex/skills/<name>/SKILL.md`.

When the user explicitly invokes or clearly implies one of these workflow commands, read the matching skill file and follow it:

- `/git-init`, `/git-commit`
- `/init-project`, `/build-ai`, `/update-ai`, `/setup-testing`
- `/new-change`, `/continue-change`, `/check-changes`
- `/review-tests`, `/fix-bug`, `/archive-change`, `/ask-codebase`

Treat `.Codex/skills/<name>/SKILL.md` as the workflow playbook set for this repository.

The existing root-level tool skills remain useful for domain-specific commands, but project workflow orchestration should come from `.Codex/skills/`.

| Skill | 说明 | 触发关键词 |
| ----- | ---- | ---------- |
| **wechat-article-to-markdown** | 抓取微信公众号文章 | `wechat`、`微信`、`公众号`、`抓取微信` |
| **github-tools** | 抓取 GitHub 仓库信息 | `github`、`搜仓库`、`gh search` |
| **papers-tools** | 抓取 arXiv 论文 | `论文`、`arXiv`、`paper`、`抓取论文` |

## Key Commands

### 收集

```bash
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

## Tech Stack

- Python 3.10+ with `uv` for dependency management
- Camoufox (反检测浏览器) for WeChat article fetching
- BeautifulSoup + markdownify for HTML→Markdown conversion
- arXiv public API for paper fetching
