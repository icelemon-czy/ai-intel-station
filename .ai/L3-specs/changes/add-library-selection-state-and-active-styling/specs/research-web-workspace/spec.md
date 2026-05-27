# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

[完整描述]

#### Scenario: Navigation structure

- **WHEN** 用户访问 Web Workspace
- **THEN** 导航栏显示 Dashboard、Library、Briefing 和 Collect 四个主要入口，点击切换对应工作区

#### Scenario: Active state indication

- **WHEN** 用户在导航栏点击某个入口
- **THEN** 该入口显示 active 状态样式，其他入口保持默认样式

### Requirement: Library Interaction States

[新增]

#### Scenario: Library result item active state

- **WHEN** 用户点击 Library 结果列表中的某个项
- **THEN** 该项显示明确的选中样式，其他项保持默认样式

#### Scenario: Library result item hover state

- **WHEN** 用户鼠标悬停在 Library 结果列表中的某个项
- **THEN** 该项显示 hover 样式，提示用户该项可点击