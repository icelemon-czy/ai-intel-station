# 统一研究入口

## 适用任务

- 调整 collect / query / briefing / backfill 的根级命令表面
- 统一旧来源工具命令到一个 operator surface
- 排查“该从哪条命令进系统”的运行时问题

## 入口与关键文件

- `research/cli.py` — 唯一 operator-facing 入口
- `pyproject.toml` — 暴露 `research` console script
- `collect/` — 被 operator surface 调度的来源收集层
- `library/` — 被 operator surface 调度的 query / backfill 层
- `briefing/` — 被 operator surface 调度的 briefing 层

## 主数据流

```text
research <command> ...
  ├─ collect github / papers / wechat
  ├─ query <keyword>
  ├─ briefing digest|reading-list <keyword>
  └─ backfill [output_root]
```

## 关键约束

- 对外只保留这一层作为运行入口
- `query` 和 `briefing` 只消费本地 sidecar，不重新抓远端数据
- `briefing` 只写 `output/briefing/`
- 多来源覆盖不完整时，允许继续产生结果，但必须显式写出缺口

## 验证

```bash
uv run research --help
uv run research collect papers --list
uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output
```