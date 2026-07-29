# Daily Discovery — Delta Spec

> 本文件描述对 `specs/daily-discovery/spec.md` 的增量变更。

## MODIFIED Requirements

### Requirement: Persistent Run Log and Read-Only Status

每次 discovery SHALL 在 configurable local state directory 中记录 run summary，未配置 `log_dir` 时默认目录 MUST 为 repository-local `.state/discovery/`；status 和 log-list MUST 只读 configured directory 中的已有 log。任意显式 `log_dir` SHALL 继续有效，包括旧模板值 `.ai/L4-session/discovery/`。migration 不得新增自动搬迁或删除动作；active directory 既有的 `max_log_files` retention 语义保持不变。

#### Scenario: Write a run to the new default directory

- **WHEN** operator 未配置 `log_dir` 并运行 discovery
- **THEN**run summary 写入 repository-local `.state/discovery/`

#### Scenario: Inspect previous runs from the configured directory

- **WHEN**configured directory 已有 run log，operator 分别运行 `discover --status` 和 `discover --log-list`
- **THEN**两个 action 均从 configured directory 返回已有 summary
- **AND**不会执行 network 或新的 discovery

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
