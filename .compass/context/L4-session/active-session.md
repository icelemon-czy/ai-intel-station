# 当前会话状态

> 这里只维护当前 baseline、active pointer 与下一步方向；历史 change 证据位于 L3 archive
> 和 L5 reports，不在本文件重复堆叠。

## 最后更新

- **时间**: 2026-08-16
- **主题**: Classify briefing by source
- **状态**: `classify-briefing-by-source` 已归档；无 active L3 change

## 当前 baseline

- primary interface 是 Agent + project-local Skill。
- `.agents/skills/daily-discovery/SKILL.md` 负责 Today、Preferences、Status 与明确请求的 Schedule。
- `research` CLI 是 deterministic runtime；local archive、ResearchItem sidecar、briefing 与 run log
  是 data source of truth。
- daily quota briefing 按 collect `source` 分组：default 3 Hacker News + optional max 2 WeChat +
  0 X + 1 GitHub + 1 arXiv。`news` 不再是用户可见 lane；destination host 不再改变归属。
- Web 保留为 optional Library / briefing viewer，不是 normal discovery 的前置条件。
- default `uv sync --frozen` 只保留 project + PyYAML；WeChat browser stack 通过
  `uv sync --extra wechat` 按需安装；pytest 通过 `dev` extra 安装。
- active context 位于 `.compass/context/`，canonical Workflow 位于 `.agents/skills/`，
  runtime state 位于 `.state/discovery/`。

## 最近完成

- `classify-briefing-by-source` 已合并到 briefing、signal-discovery、daily-discovery、
  github 与 papers 主 Specs，并归档。
- 相关测试：pytest 110 passed / 4 subtests；discovery runner unittest 15 passed。

## 已知 gap

- Codex 本机 automation prompt 若仍写 “5 News”，不在本仓库内，需另改。
- WeChat live e2e 未运行，因为没有 operator-provided `WECHAT_E2E_URLS`。

## 下一步方向

先 dogfood 按 source 分组的 daily briefing；观察 HN GitHub-target story 与 optional WeChat
是否符合阅读习惯。

## Workspace

- 本轮未要求 commit / push。
