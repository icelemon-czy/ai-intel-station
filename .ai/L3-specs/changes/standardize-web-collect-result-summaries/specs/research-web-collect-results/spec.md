# research-web-collect-results — Delta Spec

> 本文件描述对 `specs/research-web-collect-results/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 统一 Collect 结果结构

所有 source 的 collect 结果必须返回统一结构。

#### Scenario: GitHub collect 返回统一结果

- **WHEN** GitHub collect 完成
- **THEN** 返回 `{status: "success"|"error", message: string, item_count?: number, saved_paths?: string[]}`

#### Scenario: Papers collect 返回统一结果

- **WHEN** Papers collect 完成
- **THEN** 返回 `{status: "success"|"error", message: string, item_count?: number, saved_paths?: string[]}`

#### Scenario: WeChat collect 返回统一结果

- **WHEN** WeChat collect 完成
- **THEN** 返回 `{status: "success"|"error"|"partial", message: string, item_count?: number, saved_paths?: string[]}`

### Requirement: 结果状态区分

Collect 结果区分不同状态。

#### Scenario: 成功时显示 item_count 和 saved_paths

- **WHEN** collect 成功
- **THEN** 结果包含 item_count 和 saved_paths 列表

#### Scenario: 失败时显示错误信息

- **WHEN** collect 失败
- **THEN** 结果包含 status: "error" 和错误描述