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

GitHub collection SHALL 支持 repository search，并将一组结果保存在可查询的本地 artifact 中。

#### Scenario: Search repositories

- **WHEN** operator 以 search mode 提交 query
- **THEN**系统写入 GitHub source tree 下的 search Markdown
- **AND**对应 ResearchItem 集合可以被 Library 加载

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
