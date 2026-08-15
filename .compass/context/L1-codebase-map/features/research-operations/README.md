# 统一研究入口

## 适用任务

- 调整 collect / query / briefing / backfill / discover / status / schedule 的根级命令表面
- 统一旧来源工具命令到一个 operator surface
- 排查“该从哪条命令进系统”的运行时问题

## 入口与关键文件

- `.agents/skills/daily-discovery/SKILL.md` — primary Agent-first daily intelligence surface
- `research/cli.py` — 唯一 operator-facing 入口
- `pyproject.toml` — 暴露 `research` console script
- `collect/` — 被 operator surface 调度的来源收集层
- `library/` — 被 operator surface 调度的 query / backfill 层
- `briefing/` — 被 operator surface 调度的 briefing 层

## 主数据流

```text
自然语言 intent
  → daily-discovery Skill
  → research <command> ...
  ├─ collect github / papers / wechat
  ├─ discover [github|papers|wechat|hackernews|x]
  ├─ query <keyword>
  ├─ briefing digest|reading-list <keyword>
  └─ backfill [output_root]
  → Agent 读取 local artifact 并返回重点
```

## 关键约束

- 对外只保留这一层作为运行入口
- Agent 执行 command 并解释 artifact；normal daily flow 不要求 user 编排 CLI 或启动 Web
- default environment 不包含 optional WeChat browser stack 或 pytest
- `query` 和 `briefing` 只消费本地 sidecar，不重新抓远端数据
- `briefing` 只写 `output/briefing/`
- 多来源覆盖不完整时，允许继续产生结果，但必须显式写出缺口
- Hacker News / X 是 discovery-only selector，不扩展 standalone collect subcommand
- signal briefing 的 source status 必须和 item confidence 分开；coverage failure 不能装成 quiet day

## 验证

```bash
uv run research --help
uv run research collect papers --list
uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research discover --dry-run
uv run research discover --source hackernews --source wechat
uv run research discover --status
uv run research backfill output
```
