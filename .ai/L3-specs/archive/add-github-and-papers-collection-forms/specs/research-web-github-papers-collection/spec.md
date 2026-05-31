# research-web-github-papers-collection — Delta Spec

> 本文件描述对 `specs/research-web-github-papers-collection/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: GitHub 采集表单

Web Collect Workspace 应提供 GitHub 专用的采集表单，支持 repo 模式和 search 模式。

#### Scenario: GitHub Repo 模式

- **WHEN** 用户在 GitHub source 下选择 repo 模式
- **THEN** 显示 owner/repo 输入框，提示格式为 `owner/repo`
- **THEN** 表单校验要求输入符合 `owner/repo` 格式，否则显示格式错误提示

#### Scenario: GitHub Search 模式

- **WHEN** 用户在 GitHub source 下选择 search 模式
- **THEN** 显示搜索关键词输入框和 max results 输入框
- **THEN** 搜索关键词为必填，max results 默认为 10

#### Scenario: GitHub 表单校验

- **WHEN** 用户提交 GitHub 表单但格式不正确
- **THEN** 显示 source-specific 错误提示，不提交请求

### Requirement: Papers 采集表单

Web Collect Workspace 应提供 papers 专用的采集表单，支持 category 选择和多 category 组合。

#### Scenario: Papers Category 选择

- **WHEN** 用户在 Papers source 下
- **THEN** 显示 category 输入框，提示常用 category 如 cs.AI, cs.LG, cs.CL
- **THEN** 显示 max results 输入框，默认为 10

#### Scenario: Papers 多 Category 支持

- **WHEN** 用户在 Papers source 下输入多个 category
- **THEN** 支持以逗号分隔输入多个 category
- **THEN** 系统依次查询每个 category 的最新论文

#### Scenario: Papers 表单校验

- **WHEN** 用户提交 Papers 表单但 category 为空
- **THEN** 显示错误提示"Category 是必填字段"
- **THEN** 不提交请求

### Requirement: Source-Specific 错误反馈

每个 source 的表单应提供清晰的错误提示和成功反馈。

#### Scenario: 采集成功反馈

- **WHEN** 采集任务成功完成
- **THEN** 显示成功提示和采集到的 items 数量

#### Scenario: 采集失败反馈

- **WHEN** 采集任务失败
- **THEN** 显示 source-specific 错误信息，说明失败原因