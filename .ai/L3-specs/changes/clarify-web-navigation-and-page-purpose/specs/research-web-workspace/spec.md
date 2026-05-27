# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Navigation

[完整描述]

#### Scenario: Navigation structure

- **WHEN** 用户访问 Web Workspace
- **THEN** 导航栏使用用户目标导向的命名：资料总览、资料库、生成简报、采集资料
- **THEN** 点击导航项切换到对应工作区

#### Scenario: Active state indication

- **WHEN** 用户在导航栏点击某个入口
- **THEN** 该入口显示 active 状态样式，其他入口保持默认样式

### Requirement: Page Purpose Display

[新增]

#### Scenario: Page title and description

- **WHEN** 用户进入任何工作区页面
- **THEN** 页面顶部显示清晰的页面标题和简短用途说明

#### Scenario: Navigation CTA

- **WHEN** 工作区页面需要引导用户继续操作
- **THEN** 显示下一步 CTA 按钮，链接到相关工作区