# research-web-local-open-actions — Delta Spec

> 本文件描述对 `specs/research-web-local-open-actions/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 本地文件打开动作

从 Web 可触发本地归档路径的文件管理器打开动作。

#### Scenario: Open local folder 动作

- **WHEN** 用户在 Library detail 面板点击 "Open local folder"
- **THEN** 打开 item 对应的本地归档目录（如 Finder）

#### Scenario: Open Markdown content

- **WHEN** 用户在 Library detail 面板点击 "View Markdown"
- **THEN** 使用系统默认应用打开本地 Markdown 文件