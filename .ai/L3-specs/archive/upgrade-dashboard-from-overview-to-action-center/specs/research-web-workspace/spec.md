# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

The Web workspace SHALL provide a navigation structure that exposes Dashboard, Library, Briefing, and Collect as the primary entry points, with active state indication on selection.

#### Scenario: Navigation structure

- **WHEN** the operator opens the Web workspace
- **THEN** the navigation bar displays entries labeled by user goals: Dashboard (资料总览), Library (资料库), Briefing (生成简报), Collect (采集资料)
- **AND** clicking each entry switches to the corresponding workspace section

#### Scenario: Active state indication

- **WHEN** the operator clicks on a navigation entry
- **THEN** that entry displays an active visual state and the corresponding workspace section is rendered
- **AND** other entries remain in their default visual state

### Requirement: Dashboard Action Center

[新增]

#### Scenario: Dashboard shows action-oriented content

- **WHEN** 用户访问 Dashboard
- **THEN** Dashboard 显示任务摘要、数据 freshness、行动入口卡片
- **THEN** 而不是仅仅显示静态统计数字

#### Scenario: Dashboard CTA cards

- **WHEN** Dashboard 显示行动入口卡片
- **THEN** 卡片包含图标、标题和简短描述
- **THEN** 点击卡片导航到对应工作区