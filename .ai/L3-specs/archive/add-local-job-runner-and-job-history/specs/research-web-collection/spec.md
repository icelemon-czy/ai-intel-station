# research-web-collection — Delta Spec

> 本文件描述对 `specs/research-web-collection/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Collect Workspace 页面

The Web workspace SHALL provide a dedicated Collect Workspace page as the unified entry point for ingesting research material from multiple sources.

#### Scenario: 用户导航到采集工作台

- **WHEN** 用户点击导航中的"采集"入口
- **THEN** 页面加载采集工作台，显示 source 切换器、输入区域、运行状态区域和结果摘要区域

#### Scenario: 用户切换采集来源

- **WHEN** 用户在采集工作台中选择不同的 source（WeChat / GitHub / Papers）
- **THEN** 输入区域和可用字段随 source 变化，页面保持工作台布局不变

#### Scenario: 用户提交采集任务

- **WHEN** 用户填写完 source 对应字段并提交
- **THEN** 创建新任务并进入 queued 状态，运行状态区域显示任务进度
- **AND** 任务完成后结果摘要区域展示采集结果

### Requirement: 采集工作台与导航一致性

The Collect Workspace SHALL maintain consistent navigation semantics and page descriptions with Dashboard, Library, and Briefing.

#### Scenario: 采集工作台页面说明

- **WHEN** 用户进入采集工作台
- **THEN** 页面顶部显示清晰的页面标题和简短说明，告知用户当前所在工作流位置

### Requirement: Source 表单接入框架

The Collect Workspace SHALL provide a unified source form integration framework into which individual source forms can be plugged incrementally.

#### Scenario: Source 表单区域渲染

- **WHEN** 用户选择某个 source
- **THEN** 系统渲染该 source 对应的表单组件，表单字段与该 source 的采集参数对应

### Requirement: Job-based 执行模型

[新增]

#### Scenario: 采集表单提交创建 Job

- **WHEN** 用户填写采集表单并提交
- **THEN** 系统创建 Job 记录，表单数据作为 Job 参数
- **THEN** 用户看到 Job 已提交的状态反馈

#### Scenario: Job 状态实时更新

- **WHEN** Job 状态发生变化（queued → running → success/failed）
- **THEN** 采集工作台的运行状态区域实时更新显示当前状态