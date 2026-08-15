# Local Library Specification

## Purpose

把不同来源的 sidecar 统一为可复用的 local research library，并支持历史 archive backfill 与本地查询。

## Requirements

### Requirement: Unified ResearchItem

Library SHALL 使用一个 backward-compatible ResearchItem contract 表示 archive item、realtime
signal 与 supporting evidence。除 source、item type、title、canonical URL 与 output path 外，
contract SHALL 允许 `discovered_at`、`signal_role` 与 `discovery_method`，以区分 observation
time / publication time 与 signal / evidence。

#### Scenario: Load items from different sources

- **WHEN** Library 扫描多个 legacy 与 current source tree
- **THEN**所有有效 sidecar 被解析为统一 item shape
- **AND**缺少新增 optional field 不会破坏 legacy sidecar

#### Scenario: Save a newly discovered signal

- **WHEN** realtime collector 第一次观测 source item
- **THEN**sidecar 记录 `discovered_at`、`signal_role=signal` 与 discovery method
- **AND**source publication time 仍由 `published_at` 独立表示

#### Scenario: Observe the same canonical item again

- **WHEN** collector 在后续 run 再次看到已归档 canonical item
- **THEN**保留首次 `discovered_at`
- **AND**mutable source metadata MAY 刷新，但不得把 item 伪装成新发现

#### Scenario: Backfill historical archive

- **WHEN** backfill 从历史 Markdown 重建 sidecar
- **THEN**不捏造当前 `discovered_at`
- **AND**历史 item 不能伪装成新发现内容

### Requirement: Partial Metadata Is Allowed

缺少非核心 metadata 的 ResearchItem MAY 被保存和查询。

#### Scenario: Source omits optional fields

- **WHEN** collected item 缺少 authors、tags、summary 或 timestamp
- **THEN**sidecar 仍可加载
- **AND**缺失字段不会导致整个 Library failure

### Requirement: Sidecar and Markdown Association

每个 ResearchItem MUST 指向 source archive 中对应的 Markdown artifact。

#### Scenario: Open item detail

- **WHEN** operator 在 Library 选择一个 item
- **THEN**item detail 指向其已保存 Markdown path
- **AND**不会把未知文件当作该 item 的 archive

### Requirement: Historical Backfill

backfill SHALL 从既有 Markdown archive 重建缺失 sidecar，且 MUST NOT 改写原始 Markdown。

#### Scenario: Backfill an old archive

- **WHEN** operator 对包含历史 Markdown 的 output tree 运行 backfill
- **THEN**系统为可识别 artifact 写入 sidecar
- **AND**原始 Markdown 内容保持不变

### Requirement: Local Query

Library SHALL 按 keyword、source 和 optional time window 查询本地 sidecar。

#### Scenario: Filter local items

- **WHEN** operator 提交 keyword、source 或 date filter
- **THEN**结果只包含匹配的本地 ResearchItem
- **AND**查询不触发 remote fetch

### Requirement: Resilient Sidecar Loading

单个 malformed、BOM-encoded 或缺失文件的 sidecar SHOULD 被隔离，不应使整个 Library 无法使用。

#### Scenario: One sidecar is malformed

- **WHEN**扫描过程中遇到无法解析的 sidecar
- **THEN**其他有效 item 仍被返回
- **AND**坏文件不会被静默当作有效 item
