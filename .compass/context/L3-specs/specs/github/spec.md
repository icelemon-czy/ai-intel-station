# GitHub Collection Specification

## Purpose

从 GitHub repository 或 repository search 生成本地研究 archive。

## Requirements

### Requirement: Repository Snapshot

GitHub collection SHALL 将一个 `owner/repo` 保存为包含来源 metadata 的 Markdown snapshot。

#### Scenario: Collect one repository

- **WHEN** operator 提交有效 `owner/repo`
- **THEN**系统写入 `output/github/<owner-repo>/README.md`
- **AND**内容包含 canonical repository URL、summary 和可用 metadata

### Requirement: Repository Search Snapshot

GitHub collection SHALL 支持 repository search，并将结果保存为 recency-oriented supporting
evidence。Search MUST 请求并保存可用 creation/update timestamp，且不得把 lifetime stars
ordering 表述为 daily trend signal。

#### Scenario: Search repositories

- **WHEN** operator 或 discovery runtime 以 search mode 提交 query
- **THEN**系统按 recent update 请求结果，并写入 search Markdown 与 sidecar
- **AND**每个结果保存可用 creation/update time 与 `signal_role=evidence`

#### Scenario: Persist search output path

- **WHEN** repository search artifact 与 sidecar 写入成功
- **THEN**collection function 返回真实 Markdown Path
- **AND**discovery run report 不会把缺失 output path 序列化为成功

### Requirement: Optional Issue Coverage

operator MAY 请求在 repository snapshot 中包含 open issue 信息。

#### Scenario: Collect with issues enabled

- **WHEN** operator 启用 issue collection 且 repository 有 open issues
- **THEN**生成的 snapshot 包含返回的 open issue 信息

### Requirement: GitHub Sidecars

GitHub repository 和 search artifact MUST 生成包含 `source=github`、canonical URL 与 output path 的 sidecar。

#### Scenario: Load a collected repository in Library

- **WHEN** repository snapshot collection 成功
- **THEN**其 sidecar 可由 local Library 加载
- **AND**output path 指向已保存 Markdown

### Requirement: Explicit GitHub CLI Failure

GitHub collection MUST 暴露 `gh` 的失败原因。

#### Scenario: GitHub CLI returns non-zero

- **WHEN** `gh` command 返回 non-zero
- **THEN**当前 operation 失败并包含可操作的 stderr context

### Requirement: GitHub Evidence Role

GitHub repository snapshot 与 search result SHALL 保留 `signal_role=evidence`；缺少该字段的
legacy GitHub item SHALL 也被解释为 evidence。GitHub evidence MUST NOT 独立 seed 或填充
Hacker News / WeChat / X source quota，但 verified fresh GitHub evidence MAY 在 configured
GitHub section 作为 primary reading entry。

#### Scenario: A fresh repository has no social signal

- **WHEN** GitHub repository 有 verifiable recent source activity，但没有 matching realtime signal
- **THEN**它 MAY 以 `low` confidence 占据 dedicated GitHub quota
- **AND**它不消耗 Hacker News / WeChat / X slot，也不声称 social corroboration

