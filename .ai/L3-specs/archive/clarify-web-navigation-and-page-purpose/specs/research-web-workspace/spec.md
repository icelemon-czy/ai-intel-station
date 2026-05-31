# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

The Web workspace SHALL provide a navigation structure that exposes Dashboard, Library, Briefing, and Collect as the primary entry points, with user-goal-oriented labeling and active state indication on selection.

#### Scenario: Navigation structure

- **WHEN** the operator opens the Web workspace
- **THEN** the navigation bar displays entries labeled by user goals: Dashboard (资料总览), Library (资料库), Briefing (生成简报), Collect (采集资料)
- **AND** clicking each entry switches to the corresponding workspace section

#### Scenario: Active state indication

- **WHEN** the operator clicks on a navigation entry
- **THEN** that entry displays an active visual state and the corresponding workspace section is rendered
- **AND** other entries remain in their default visual state

### Requirement: Page Purpose Display

[新增]

#### Scenario: Page title and description

- **WHEN** 用户进入任何工作区页面
- **THEN** 页面顶部显示清晰的页面标题和简短用途说明

#### Scenario: Navigation CTA

- **WHEN** 工作区页面需要引导用户继续操作
- **THEN** 显示下一步 CTA 按钮，链接到相关工作区