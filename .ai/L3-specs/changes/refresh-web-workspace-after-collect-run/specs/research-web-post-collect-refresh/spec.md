# research-web-post-collect-refresh — Delta Spec

> 本文件描述对 `specs/research-web-post-collect-refresh/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Collect 后自动刷新 Library

Collect 成功后，Library 应该自动刷新显示最新结果。

#### Scenario: 采集成功后刷新 Library 结果

- **WHEN** 用户在 Collect Workspace 成功完成一次采集
- **THEN** Library 的搜索结果自动刷新，用户可以看到最新采集的资料

#### Scenario: Collect 后显示 CTA

- **WHEN** 用户完成采集
- **THEN** 显示"去 Library 查看"或"查看新增内容"等下一步动作引导

### Requirement: Collect 后刷新 Dashboard 统计

采集新资料后，Dashboard 的统计数字应立即更新。

#### Scenario: Dashboard total_count 增加

- **WHEN** 新增了 research item
- **THEN** Dashboard 的 total_items 统计相应增加