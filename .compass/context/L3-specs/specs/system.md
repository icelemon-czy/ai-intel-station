# AI Intel Station System Specification

## Purpose

AI Intel Station 是一个 local-first AI 研究工作区。它从受支持的外部来源收集资料，以本地 archive 作为共同事实来源，并生成可供人阅读的 briefing。

## System Boundary

系统负责：

- 从 GitHub、arXiv 和 WeChat 收集内容
- 维护本地 Markdown archive 与 ResearchItem sidecar
- 查询本地资料库并生成 briefing
- 提供 CLI、local Web workspace 和 daily discovery 自动化入口

系统不负责：

- remote multi-user service
- 云端 account、同步或权限系统
- 尚未实现的 Twitter ingestion
- 通用 Web job history、任意 cron CRUD 或 diagnostics dashboard

## Requirements

### Requirement: Local-First Operation

系统 SHALL 在本地执行资料收集、查询、briefing 和自动 discovery，并将持久结果保存在项目配置的本地路径中。

#### Scenario: Operator completes a research workflow

- **WHEN** operator 通过受支持入口执行 collect、query、briefing 或 discover
- **THEN**系统在本地完成业务流程
- **AND**不要求连接 AI Intel Station 自身的 remote service

### Requirement: Shared Local Archive Truth

CLI、Web workspace 和 daily discovery SHALL 读取同一 `output_root` 下的 archive 与 ResearchItem sidecar。

#### Scenario: Collected item becomes available to all surfaces

- **WHEN**任一入口成功写入 ResearchItem sidecar
- **THEN**后续 CLI query、Web Library 和 briefing 可以从同一 archive 读取该条目
- **AND**不需要重新抓取远端来源

### Requirement: Raw and Derived Output Separation

原始来源 archive MUST 与派生 briefing 分离。

#### Scenario: Save raw and derived artifacts

- **WHEN** collect 成功
- **THEN**source archive 写入 `output/github|papers|wechat|hackernews|x/`
- **AND** briefing 只写入 `output/briefing/`

### Requirement: Unified Documented Entrypoint

每个受支持 capability SHALL 能通过统一 `research` command surface 或其 local Web surface 到达，并在 project documentation 中可发现。

#### Scenario: Operator follows documented commands

- **WHEN** operator 按 README 或 Compass context 中的命令操作
- **THEN**命令进入统一 workspace surface
- **AND**不要求调用已移除的 source-specific top-level wrapper

### Requirement: Explicit and Partial Failure Reporting

系统 MUST 明确报告 external dependency 或输入失败；当一次操作包含多个独立来源或步骤时，系统 SHOULD 保留成功部分并说明失败部分。

#### Scenario: One part of a multi-source operation fails

- **WHEN**一个来源失败而其他来源成功
- **THEN**结果明确列出失败来源和原因
- **AND**已成功的 archive 或 briefing 结果仍可使用
