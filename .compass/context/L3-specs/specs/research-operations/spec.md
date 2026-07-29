# Research Operations Specification

## Purpose

定义 operator 面向 AI Intel Station 的统一 command surface，以及 CLI 与 local Web workspace 的职责边界。

## Requirements

### Requirement: Unified Command Surface

workspace SHALL 通过 `research` command surface 暴露 `collect`、`query`、`briefing`、`backfill`、`web`、`discover`、`schedule` 和 `init-config`。

#### Scenario: List supported operations

- **WHEN** operator 运行 `research --help`
- **THEN**输出列出所有受支持的顶层 action

#### Scenario: Dispatch collection by source

- **WHEN** operator 运行 `research collect github|papers|wechat`
- **THEN** command dispatch 到对应 collection capability
- **AND**不要求使用 source-specific wrapper script

### Requirement: Local Read Actions Avoid Remote Fetch

`query`、`briefing`、`backfill` inspection 和 briefing listing SHALL 只使用本地 archive 或 sidecar。

#### Scenario: Query local library

- **WHEN** operator 运行 `research query`
- **THEN**结果来自本地 ResearchItem sidecar
- **AND**不会访问 GitHub、arXiv 或 WeChat

### Requirement: Local Web Workspace Entry

`research web` SHALL 启动读取指定 `output_root` 的 local Web workspace，并清晰报告实际使用的 archive path。

#### Scenario: Start Web workspace from a nested working directory

- **WHEN** operator 使用相对 `output_root` 启动 Web workspace
- **THEN** server 将路径解析到 project root 下的 archive
- **AND** Dashboard 与 Library 使用该解析后的路径

### Requirement: Read-Only Operational Inspection

status、log list 和 briefing list action SHALL 在不重新执行 collect 或 discover 的情况下返回已有本地状态。

#### Scenario: Inspect the latest discovery run

- **WHEN** operator 运行 discovery status 或 log-list
- **THEN** command 读取已有 run log
- **AND**不触发 network 或新的 collection

### Requirement: Lightweight Core Runtime

default project environment SHALL 支持 GitHub、Papers、local query、briefing 与 discovery
control actions，而不安装 WeChat browser stack 或 test-only dependency；source-specific
optional dependency MUST NOT 阻止 core command surface 启动。

#### Scenario: Bootstrap the default operator environment

- **WHEN** fresh environment 只安装 project default dependency
- **THEN**base install 不包含 Camoufox、Playwright、BeautifulSoup、markdownify、httpx 或 pytest
- **AND**`research --help` 与 network-free `research discover --dry-run` 可以启动

#### Scenario: Install an optional source runtime

- **WHEN**operator 明确安装 `wechat` extra
- **THEN**WeChat collection 所需 browser、HTML conversion 与 image download dependency 被安装
- **AND**core command contract 保持不变
