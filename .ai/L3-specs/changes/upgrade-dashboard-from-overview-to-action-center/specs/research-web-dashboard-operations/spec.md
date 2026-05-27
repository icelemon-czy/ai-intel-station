# research-web-dashboard-operations — Delta Spec

> 本文件描述对 `specs/research-web-dashboard-operations/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Dashboard 任务摘要

Dashboard 应显示最近任务的状态摘要，帮助用户快速了解系统状态。

#### Scenario: 最近任务列表

- **WHEN** 用户访问 Dashboard
- **THEN** 显示最近 5 个任务的状态（成功/失败/进行中）
- **THEN** 失败任务显示红色标识和错误摘要

#### Scenario: 任务状态颜色标识

- **WHEN** Dashboard 显示任务列表
- **THEN** 成功任务显示绿色标识
- **THEN** 失败任务显示红色标识
- **THEN** 进行中任务显示黄色/蓝色标识

### Requirement: 数据 Freshness

Dashboard 应显示本地数据的 freshness，帮助用户判断是否需要刷新。

#### Scenario: 数据时间戳显示

- **WHEN** Dashboard 显示数据项
- **THEN** 显示每类 source 的最后采集时间
- **THEN** 如果某 source 超过 7 天未采集，显示"可能过时"提示

#### Scenario: 数据缺失提示

- **WHEN** Dashboard 发现某 source 从未采集
- **THEN** 显示"缺少 [source] 数据，建议去采集"

### Requirement: Dashboard CTA

Dashboard 应提供明确的行动入口，引导用户完成工作流。

#### Scenario: 行动入口卡片

- **WHEN** 用户访问 Dashboard
- **THEN** 显示行动入口卡片："去采集资料"、"去资料库搜索"、"生成简报"
- **THEN** 每个入口卡片点击后导航到对应页面

#### Scenario: 推荐动作

- **WHEN** Dashboard 发现数据缺失或过时
- **THEN** 在相应区域显示推荐动作，如"缺少 WeChat 数据，去采集"

### Requirement: 依赖状态摘要

Dashboard 应显示关键依赖的可用性状态。

#### Scenario: 依赖状态指示

- **WHEN** Dashboard 加载
- **THEN** 显示 GitHub CLI、WeChat 浏览器等依赖的状态
- **THEN** 不可用时显示修复建议