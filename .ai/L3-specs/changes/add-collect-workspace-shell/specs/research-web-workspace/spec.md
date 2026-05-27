# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

[完整描述从主 spec 复制]

#### Scenario: Navigation structure

- **WHEN** 用户访问 Web Workspace
- **THEN** 导航栏显示 Dashboard、Library、Briefing 和 Collect 四个主要入口，点击切换对应工作区

#### Scenario: Active state indication

- **WHEN** 用户在导航栏点击某个入口
- **THEN** 该入口显示 active 状态样式，其他入口保持默认样式

### Requirement: Web Workspace Page Layout

[完整描述从主 spec 复制]

#### Scenario: Consistent panel styling

- **WHEN** 工作区页面渲染多个面板
- **THEN** 所有面板使用一致的圆角、间距和阴影样式

#### Scenario: Responsive grid layout

- **WHEN** 工作区页面在不同宽度窗口展示
- **THEN** 面板网格响应式调整，保持可读性和可用性