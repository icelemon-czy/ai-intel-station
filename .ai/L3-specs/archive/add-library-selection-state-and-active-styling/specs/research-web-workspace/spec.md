# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

The Web workspace SHALL provide a navigation structure that exposes Dashboard, Library, Briefing, and Collect as the primary entry points, with active state indication on selection.

#### Scenario: Navigation structure

- **WHEN** the operator opens the Web workspace
- **THEN** the navigation bar displays Dashboard, Library, Briefing, and Collect as the four primary entry points
- **AND** clicking each entry switches to the corresponding workspace section

#### Scenario: Active state indication

- **WHEN** the operator clicks on a navigation entry
- **THEN** that entry displays an active visual state and the corresponding workspace section is rendered
- **AND** other entries remain in their default visual state

### Requirement: Library Interaction States

[新增]

#### Scenario: Library result item active state

- **WHEN** 用户点击 Library 结果列表中的某个项
- **THEN** 该项显示明确的选中样式，其他项保持默认样式

#### Scenario: Library result item hover state

- **WHEN** 用户鼠标悬停在 Library 结果列表中的某个项
- **THEN** 该项显示 hover 样式，提示用户该项可点击