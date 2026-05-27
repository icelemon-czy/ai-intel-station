# research-web-scheduling — Delta Spec

> 本文件描述对 `specs/research-web-scheduling/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Schedule 配置模型

系统应提供定时采集和刷新策略的配置能力。

#### Scenario: 创建 Schedule

- **WHEN** 用户创建一个新的定时采集任务
- **THEN** 系统记录 schedule 配置，包括：source、参数、频率、下次执行时间、启用/停用状态

#### Scenario: Schedule 频率选项

- **WHEN** 用户配置 schedule 频率
- **THEN** 支持的选项包括：每天、每周、每月、自定义 cron 表达式
- **THEN** 系统根据频率计算下次执行时间

#### Scenario: Schedule 启停控制

- **WHEN** 用户启用或停用一个 schedule
- **THEN** 启用的 schedule 按设定频率执行
- **THEN** 停用的 schedule 不执行，但仍保留配置

#### Scenario: Schedule 与 Jobs 联动

- **WHEN** 一个 schedule 到期触发执行
- **THEN** 系统创建新的 Job，关联到原 schedule
- **THEN** Job 的执行状态可在 Jobs 页面查看

### Requirement: Schedule 可视化

系统应在 UI 中展示 schedule 状态和下次执行时间。

#### Scenario: Schedule 列表视图

- **WHEN** 用户访问 schedule 管理页面
- **THEN** 显示所有 schedule 的列表，包含：名称、source、频率、下次执行时间、状态

#### Scenario: Schedule 状态指示

- **WHEN** schedule 页面显示 schedule 列表
- **THEN** 启用状态显示绿色指示器
- **THEN** 停用状态显示灰色指示器
- **THEN** 下次执行时间以相对时间显示（如"3小时后"）

### Requirement: Refresh Policy

系统应支持对已有资料定期刷新的策略。

#### Scenario: 配置 Refresh Policy

- **WHEN** 用户为一个 source 配置 refresh policy
- **THEN** 指定刷新频率和保留时间
- **THEN** 系统按策略定期重新采集资料

#### Scenario: Refresh 与 Schedule 共存

- **WHEN** 用户同时配置了 schedule 和 refresh policy
- **THEN** 两者独立执行，不互相干扰
- **THEN** 都在 Jobs 页面留下执行记录