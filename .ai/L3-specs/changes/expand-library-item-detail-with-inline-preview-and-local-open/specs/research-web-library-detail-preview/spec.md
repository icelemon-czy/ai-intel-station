# research-web-library-detail-preview — Delta Spec

> 本文件描述对 `specs/research-web-library-detail-preview/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Item Detail 展开信息

Library item 详情应展示更多 metadata，帮助用户快速了解item背景。

#### Scenario: 详情面板展示完整 metadata

- **WHEN** 用户在 Library 中选中了某个 item
- **THEN** 详情面板展示：title、summary、source、authors、tags、item_type、published_at、updated_at、canonical_url、archive path

#### Scenario: 不同 source 显示不同 metadata

- **WHEN** 用户查看 GitHub item 详情
- **THEN** 显示额外的仓库元数据（如 stars、language）
- **WHEN** 用户查看 paper 详情
- **THEN** 显示 authors 和 published_at
- **WHEN** 用户查看 WeChat article 详情
- **THEN** 显示 authors 和 publish time