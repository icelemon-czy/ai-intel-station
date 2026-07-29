# Papers Collection Specification

## Purpose

按受支持 arXiv category 收集最新论文，并为每篇论文生成本地 Markdown 与 sidecar。

## Requirements

### Requirement: Supported Category Discovery

papers collection SHALL 列出受支持的 AI-related arXiv category code 和 label。

#### Scenario: List categories

- **WHEN** operator 运行 papers list action
- **THEN**输出包含所有受支持 category code 和 label

### Requirement: Latest Papers by Category

operator SHALL 能为一个或多个受支持 category 请求有限数量的最新论文。

#### Scenario: Fetch one category

- **WHEN** operator 请求 `cs.AI` 和最大数量
- **THEN**系统请求该 category 的最新论文
- **AND**返回数量不超过 operator 指定上限

### Requirement: One Artifact per Paper

每篇成功解析的 paper MUST 生成独立 Markdown 与 ResearchItem sidecar。

#### Scenario: Persist fetched papers

- **WHEN**一个 category 返回一篇或多篇论文
- **THEN**系统在 `output/papers/arXiv-<category>/` 下逐篇写入 Markdown
- **AND**每个 sidecar 包含 title、authors、publication metadata、arXiv link 和 output path

### Requirement: Category Failure Isolation

单个 category failure MUST NOT 阻止其他 category 完成。

#### Scenario: Mixed category result

- **WHEN**一个请求中的 category 失败而另一个成功
- **THEN**失败 category 被报告
- **AND**成功 category 的 artifact 仍写入 archive
