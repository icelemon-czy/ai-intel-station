# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

[完整描述]

#### Scenario: Navigation structure

- **WHEN** 用户访问 Web Workspace
- **THEN** 导航栏显示资料总览、资料库、生成简报、采集资料四个入口，点击切换对应工作区

#### Scenario: Active state indication

- **WHEN** 用户在导航栏点击某个入口
- **THEN** 该入口显示 active 状态样式，其他入口保持默认样式

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