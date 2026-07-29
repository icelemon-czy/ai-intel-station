# AI Intel Station — GitHub Copilot Instructions

本项目只有两套 active source of truth：

- project context：`.compass/context/`
- Agent Workflow：`.agents/skills/`

不要恢复 `.ai/`、复制 platform-specific full Skill tree，或执行已退休的
`/new-change`、`/continue-change`、`/review-tests` 等命令。

## Request routing

当用户明确调用或语义上命中 Workflow 时，完整读取对应
`.agents/skills/<name>/SKILL.md`：

- `/init-project`、`/build-context`、`/brainstorm`、`/develop`
- `/fix-bug`、`/ask-codebase`、`/audit-tests`
- `/ralph-loop`、`/skill-creator`

每日情报使用 `.github/skills/daily-discovery/SKILL.md` thin adapter，再转到 canonical
Skill。单次 source fetch 使用 `tools/wechat|github|papers/` 下的 source playbook。

## Context loading

先读 `.compass/context/L1-codebase-map/overview.md`，再按任务需要逐层加载：

- 代码位置与依赖：`L1-codebase-map/`
- coding / testing contract：`L2-rules/`
- behavior source of truth：`L3-specs/specs/`
- active change：`L3-specs/changes/`
- resumable state：`L4-session/active-session.md`
- checked evidence：`L5-validation/`

不要因为 document 很长就假设它正确；实现前先确认 source of truth，review 时从
Requirement 与 user-visible contract 判断 code/test 是否 overfit。

## Product boundary

- primary interface 是 Agent + Skill；`research` CLI 是 deterministic runtime。
- Web 是 optional Library / briefing viewer，不是 daily discovery 前置条件。
- default core 只依赖 PyYAML；WeChat browser stack 通过 `wechat` extra 按需安装。
- local Markdown、ResearchItem sidecar、briefing 与 run log 是 data source of truth。
- runtime state 写入 `.state/`，不得写进 `.compass/context/`。
