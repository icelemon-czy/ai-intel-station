# research-web-jobs — Delta Spec

> 本文件描述对 `specs/research-web-jobs/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 本地任务模型

系统应提供本地任务模型，用于跟踪所有异步执行的操作。

#### Scenario: 任务创建

- **WHEN** 用户提交采集、简报生成或其他异步任务
- **THEN** 系统创建任务记录，包含唯一 ID、类型、来源参数、创建时间和初始状态

#### Scenario: 任务状态流转

- **WHEN** 任务从创建到完成经历不同阶段
- **THEN** 任务状态依次流转：queued → running → success / partial / failed
- **THEN** 每个状态变更都记录时间戳

#### Scenario: 任务结果记录

- **WHEN** 任务完成（无论成功或失败）
- **THEN** 任务记录包含执行结果摘要、错误信息（如有）和产物路径

### Requirement: 任务历史视图

Web 应提供任务历史页面，展示已完成和进行中的任务。

#### Scenario: 任务历史列表

- **WHEN** 用户访问任务历史页面
- **THEN** 显示所有任务的列表，按创建时间倒序排列
- **THEN** 每条任务显示：类型、来源参数、状态、创建时间和结果摘要

#### Scenario: 任务状态过滤

- **WHEN** 用户在任务历史页面选择状态过滤
- **THEN** 只显示该状态下的任务（如只显示 failed）

#### Scenario: 任务详情查看

- **WHEN** 用户点击某个任务
- **THEN** 显示任务详细信息，包括完整参数、执行日志和结果

### Requirement: 任务重试

对于失败或部分失败的任务，用户应能发起重试。

#### Scenario: 任务重试

- **WHEN** 用户点击失败任务的"重试"按钮
- **THEN** 系统创建新任务，引用原任务的参数
- **THEN** 新任务进入 queued 状态开始执行

### Requirement: Dashboard 任务摘要

Dashboard 应显示最近任务的状态摘要。

#### Scenario: Dashboard 任务小部件

- **WHEN** 用户访问 Dashboard
- **THEN** 显示最近 5 个任务的状态和结果摘要
- **THEN** 失败任务以红色标识，成功任务以绿色标识