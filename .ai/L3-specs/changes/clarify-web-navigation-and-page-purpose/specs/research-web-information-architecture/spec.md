# research-web-information-architecture — Delta Spec

> 本文件描述对 `specs/research-web-information-architecture/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 页面命名规范

Web 工作区的页面命名应使用用户目标导向的术语，而不是内部实现术语。

#### Scenario: Dashboard 页面命名

- **WHEN** 用户看到 Dashboard 页面
- **THEN** 页面标题为"资料总览"，说明为"查看本地 archive 的整体状态和近期简报"
- **THEN** 页面展示统计概览、近期简报入口，但不提供采集功能

#### Scenario: Library 页面命名

- **WHEN** 用户看到 Library 页面
- **THEN** 页面标题为"资料库"，说明为"搜索和浏览本地已采集的研究资料"
- **THEN** 页面提供关键词搜索、source 过滤、详情查看功能

#### Scenario: Briefing 页面命名

- **WHEN** 用户看到 Briefing 页面
- **THEN** 页面标题为"生成简报"，说明为"基于本地资料生成阅读简报"
- **THEN** 页面提供 briefing 预览和保存功能

#### Scenario: Collect 页面命名

- **WHEN** 用户看到 Collect 页面
- **THEN** 页面标题为"采集资料"，说明为"从 GitHub / Papers / WeChat 采集研究资料"
- **THEN** 页面提供 source 选择、表单输入和采集状态功能

### Requirement: 页面用途说明

每个页面应有一句话用途说明，明确"做什么 / 不做什么"。

#### Scenario: 页面说明内容

- **WHEN** 用户进入任何工作区页面
- **THEN** 页面顶部显示页面标题和简短用途说明
- **THEN** 用途说明帮助用户快速理解当前页面的作用

#### Scenario: 下一步 CTA

- **WHEN** 页面需要引导用户完成工作流
- **THEN** 显示下一步 CTA 按钮或链接，如"去采集"、"去生成简报"
- **THEN** CTA 链接到对应的工作区页面