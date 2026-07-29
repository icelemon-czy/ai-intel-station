# Daily Discovery Specification

## Purpose

通过 YAML config 组合 GitHub、Papers、WeChat 与 briefing，使 AI Intel Station 能手动或按本地 schedule 运行一次可观察的 discovery sweep。

## Requirements

### Requirement: Config Initialization and Validation

operator SHALL 能从 bundled example 创建 discovery config；无效 config MUST 一次报告所有可发现 validation problem。

#### Scenario: Initialize first-run config

- **WHEN** operator 运行 `research init-config`
- **THEN**系统从 example 写入目标 YAML
- **AND**默认不覆盖已有文件，除非 operator 明确 force

### Requirement: Network-Free Dry Run

dry-run MUST 不执行 remote collection，并 SHALL 显示计划执行的来源与 briefing。

#### Scenario: Preview a configured sweep

- **WHEN** operator 运行 `research discover --dry-run`
- **THEN**GitHub、arXiv 和 WeChat network action 不被调用
- **AND**输出与 run log 说明将执行的步骤

### Requirement: Selective and Fault-Isolated Sweep

operator SHALL 能选择一个或多个 configured source；单个来源 failure MUST 被记录且不阻止其他独立来源完成。

#### Scenario: Run selected sources

- **WHEN** operator 通过 `--source` 选择 GitHub 和 Papers
- **THEN**只运行两个选中来源
- **AND**每个来源的 collected、skipped、failed 与 notes 分别记录

### Requirement: Optional Briefing Stage

正常 discovery SHOULD 在 collection 后生成 configured briefing；operator MAY 使用 `--no-briefing` 禁用该步骤。

#### Scenario: Collect without briefing

- **WHEN** operator 运行 discover 并指定 `--no-briefing`
- **THEN**selected source 仍执行
- **AND**不会创建新的 briefing artifact

### Requirement: Persistent Run Log and Read-Only Status

每次 discovery SHALL 在 configurable local state directory 中记录 run summary，未配置 `log_dir` 时默认目录 MUST 为 repository-local `.state/discovery/`；status 和 log-list MUST 只读 configured directory 中的已有 log。任意显式 `log_dir` SHALL 继续有效，包括旧模板值 `.ai/L4-session/discovery/`。migration 不得新增自动搬迁或删除动作；active directory 既有的 `max_log_files` retention 语义保持不变。

#### Scenario: Write a run to the new default directory

- **WHEN** operator 未配置 `log_dir` 并运行 discovery
- **THEN**run summary 写入 repository-local `.state/discovery/`

#### Scenario: Inspect previous runs from the configured directory

- **WHEN**configured directory 已有 run log，operator 分别运行 `discover --status` 和 `discover --log-list`
- **THEN**两个 action 均从 configured directory 返回已有 summary
- **AND**不执行 network 或新的 discovery

#### Scenario: Preserve an explicit log directory

- **WHEN** operator 在 config 中显式设置任意 `log_dir` 并运行 discovery 与 status action
- **THEN**run log 与只读 action 使用该目录

#### Scenario: Keep the legacy template path explicit

- **WHEN** config 显式设置 `.ai/L4-session/discovery/` 且其中已有 sentinel log
- **THEN**该路径继续作为 active `log_dir`
- **AND**migration 不移动、改写或额外删除 sentinel log
- **AND**后续正常 run 仍按既有 `max_log_files` retention 处理 active directory

### Requirement: Explicit Schedule Installation

schedule action SHALL 默认只展示本地 launchd 或 cron 配置步骤；只有明确 install action MAY 修改本机 scheduler。generated cron MUST 在 fresh checkout 中先确保 default state directory 存在，再启动 discovery。

#### Scenario: Inspect schedule instructions

- **WHEN** operator 运行 schedule command 而未请求 install
- **THEN**系统打印配置内容和后续步骤
- **AND**不修改 launchd 或 crontab

#### Scenario: Run generated cron without an existing state directory

- **WHEN** generated cron 在 `.state/discovery/` 尚不存在的 repository 中执行
- **THEN**state directory 被创建
- **AND**discovery command 随后被启动

### Requirement: Web-Triggered Discovery Run

local Web workspace SHALL 能启动 discovery、查询 repository configured run status，并明确显示 config error、source result 与 briefing result。Web run 使用所选 config 时 MUST 使用该 config 的 explicit `log_dir`。

#### Scenario: Web starts discovery

- **WHEN** Dashboard 提交使用 explicit `log_dir` 的 discovery config
- **THEN**server 返回可查询的 job identifier
- **AND**run 使用该 config 的 `log_dir`
- **AND**终态记录包含 source summary 与 briefing outcome

### Requirement: Agent-Operated Daily Intelligence

project-local daily intelligence Skill SHALL 把自然语言 intent 转换为现有 `research`
action，并由 Agent 执行 action、读取 local artifact 和返回结论；normal flow MUST NOT
要求 user 自己编辑 YAML、读取 log、启动 Web 或编排 CLI。

#### Scenario: Ask what is worth reading today

- **WHEN** user 询问今天有什么值得关注，且没有明确要求 rerun
- **THEN**Agent 先只读检查今日 discovery status 与 briefing
- **AND**有今日可用 artifact 时不重复 network run
- **AND**Agent 读取 artifact 并返回最多 5 条重点及 partial failure

#### Scenario: Set up a first daily sweep

- **WHEN** user 请求首次运行或调整明确的 discovery preference
- **THEN**Agent 创建或最小修改 ignored config，并执行 network-free dry-run validation
- **AND**normal flow 不要求 user 自己编辑 YAML
- **AND**只有 user 明确请求自动 schedule 时才修改本机 scheduler
