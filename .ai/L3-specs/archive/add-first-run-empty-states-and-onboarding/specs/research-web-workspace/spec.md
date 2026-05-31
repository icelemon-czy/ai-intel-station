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

### Requirement: Web Workspace Page Layout

The Web workspace SHALL render each workspace section with consistent panel styling and a responsive grid layout.

#### Scenario: Consistent panel styling

- **WHEN** the workspace renders Dashboard, Library, Briefing, or Collect sections
- **THEN** all panels use consistent border-radius, spacing, and shadow styling across sections

#### Scenario: Responsive grid layout

- **WHEN** the workspace renders on a window with varying widths
- **THEN** the panel grid adjusts responsively to maintain readability and usability

### Requirement: Empty State Handling

[新增]

#### Scenario: Sections display empty state messages

- **WHEN** 工作区某个 section 没有数据可展示
- **THEN** 显示明确的空状态文案和下一步引导，而不是显示空白或无意义的控件

#### Scenario: Empty state shows CTA

- **WHEN** 工作区某个 section 显示空状态
- **THEN** 提供明确的 Call-to-Action 按钮或链接，引导用户完成必要的前置操作