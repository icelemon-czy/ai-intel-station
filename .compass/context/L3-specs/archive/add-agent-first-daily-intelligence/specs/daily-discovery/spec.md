# Daily Discovery — Delta Spec

> 本文件描述对 `specs/daily-discovery/spec.md` 的增量变更。
> 已于 2026-07-25 合并到 main Spec，保留为 archive evidence。

## ADDED Requirements

### Requirement: Agent-Operated Daily Intelligence

project-local daily intelligence Skill SHALL 把自然语言 intent 转换为现有 `research`
action，并由 Agent 执行 action、读取 local artifact 和返回结论；normal flow MUST NOT
要求 user 自己编辑 YAML、读取 log、启动 Web 或编排 CLI。

#### Scenario: Ask what is worth reading today

- **WHEN** user 询问今天有什么值得关注，且没有明确要求 rerun
- **THEN**Agent 先只读检查今日 discovery status 与 briefing
- **AND**有今日可用 artifact 时不重复 network run
- **AND**Agent 读取 artifact 并返回最多 5 条重点及 partial failure

#### Scenario: Set up a first daily sweep

- **WHEN** user 请求首次运行或调整明确的 discovery preference
- **THEN**Agent 创建或最小修改 ignored config，并执行 network-free dry-run validation
- **AND**normal flow 不要求 user 自己编辑 YAML
- **AND**只有 user 明确请求自动 schedule 时才修改本机 scheduler
