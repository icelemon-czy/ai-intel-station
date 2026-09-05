# AI Intel Station — GitHub Copilot Instructions

先读取 `README.md` 的 Document map，再读取相关 `doc/*_design.md`；coding 与 documentation rule 只引用 `AGENTS.md`，不要在本 adapter 复制 product fact。

## Request routing

当用户明确调用或语义上命中 Workflow 时，完整读取对应
`.agents/skills/<name>/SKILL.md`：

- `/brainstorm`、`/build-docs`、`/maintain-docs`
- `/ralph-loop`、`/skill-creator`

每日情报使用 `.github/skills/daily-discovery/SKILL.md` thin adapter，再转到 canonical
Skill。单次 source fetch 使用 `tools/wechat|github|papers/` 下的 source playbook。

不要恢复 `.compass/context/`、`.ai/`、platform-specific full Skill copy 或 standalone source CLI。所有 product operation 通过 `research` entrypoint；runtime state 只写 ignored `.state/`。
