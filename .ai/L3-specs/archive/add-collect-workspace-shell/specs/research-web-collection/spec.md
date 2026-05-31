# research-web-collection — Delta Spec

> 本文件描述对 `specs/research-web-collection/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Collect Workspace 页面

Web 应提供独立的采集工作台页面，作为将资料抓进来的统一入口。

#### Scenario: 用户导航到采集工作台

- **WHEN** 用户点击导航中的"采集"入口
- **THEN** 页面加载采集工作台，显示 source 切换器、输入区域、运行状态区域和结果摘要区域

#### Scenario: 用户切换采集来源

- **WHEN** 用户在采集工作台中选择不同的 source（WeChat / GitHub / Papers）
- **THEN** 输入区域和可用字段随 source 变化，页面保持工作台布局不变

#### Scenario: 用户提交采集任务

- **WHEN** 用户填写完 source 对应字段并提交
- **THEN** 运行状态区域显示任务进度，任务完成后结果摘要区域展示采集结果

### Requirement: 采集工作台与导航一致性

采集工作台的导航语义和页面说明应与 Dashboard、Library、Briefing 保持一致。

#### Scenario: 采集工作台页面说明

- **WHEN** 用户进入采集工作台
- **THEN** 页面顶部显示清晰的页面标题和简短说明，告知用户当前所在工作流位置

### Requirement: Source 表单接入框架

采集工作台提供统一的表单接入框架，各 source 表单可以逐步接入。

#### Scenario: Source 表单区域渲染

- **WHEN** 用户选择某个 source
- **THEN** 系统渲染该 source 对应的表单组件，表单字段与该 source 的采集参数对应