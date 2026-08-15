# Daily Discovery — Delta Spec

## MODIFIED Requirements

### Requirement: Config Initialization and Validation

operator SHALL 能从 bundled example 创建 discovery config；无效 config MUST 一次报告所有可发现
validation problem。Newly initialized signals config SHALL 对 default quota internally viable：启用并
配置至少一个 required News source、GitHub target 与 Paper category。Default WeChat watchlist MAY
保持启用以提供最多 2 条 optional News，但不得成为 config validity 或 `ready` 的前置条件。
Signals config SHALL 在 network 前验证 quota bounds/relations 与 positive required quota source
membership、enabled state 和 target availability。

#### Scenario: Initialize first-run config

- **WHEN** operator 运行 `research init-config`
- **THEN**系统从 example 写入目标 YAML
- **AND**默认不覆盖已有文件，除非 operator 明确 force

#### Scenario: Initialize a viable quota config

- **WHEN** operator 运行 `research init-config`
- **THEN**generated YAML 包含 5 News / optional maximum 2 WeChat / 1 GitHub / 1 Paper composition
- **AND**network-free dry-run 验证最多 7-item composition

#### Scenario: Positive required quota has no viable source

- **WHEN**signals config 要求的 required lane/source 不在 `briefing.sources`、disabled 或没有 configured work
- **THEN**validation 在 collection 前一次报告所有 discoverable source/quota problem
- **AND**optional WeChat maximum 不单独触发 validation failure

### Requirement: Agent-Operated Daily Intelligence

project-local daily intelligence Skill SHALL 把自然语言 intent 转换为现有 `research` action，执行它、
读取 local quota-composed artifact，并按 arXiv、GitHub 与 News 分组返回不超过 configured lane total
（default 7）的 verified fresh item，以及 required source coverage 与 quota shortfall。Normal flow
MUST NOT 把 missing required lane 表示为 complete daily briefing，也不得要求 user 自己编辑 YAML、
读取 log、启动 Web 或编排 CLI。

#### Scenario: Ask what is worth reading today

- **WHEN** user 询问今天有什么值得关注，且没有明确要求 rerun
- **THEN**Agent 先只读检查今日 discovery 与 briefing status
- **AND**dry-run、failed、stale 或 legacy empty artifact 不得伪装成今日 signal result

#### Scenario: Return the default grouped composition

- **WHEN** user 询问今天有什么值得看，且 usable quota-composed artifact 存在
- **THEN**Agent 在 default config 下返回最多 1 条 arXiv、1 条 GitHub 与 5 条 News
- **AND**News 中 WeChat 为 optional、最多 2 条；没有 WeChat 时不把它报告为 required shortfall
- **AND**每条说明它是什么与为什么现在值得看

#### Scenario: Return a partial-success briefing

- **WHEN**今日 run 有成功 signal source 且一个或多个 required source 失败
- **THEN**Agent 返回成功的 ranked item
- **AND**单独报告 succeeded、skipped 与 failed source coverage

#### Scenario: Existing Codex daily automation follows the current composition

- **WHEN**Codex automation `ai` 在每日 09:00 触发
- **THEN**prompt 要求读取或生成最多 7 条 grouped briefing，并使用 optional maximum 2 WeChat 语义
- **AND**保留 target task、schedule、真实 artifact 与 honest partial-failure 约束
- **AND**update 后 read-back 验证 task id/target、09:00 recurrence 与完整 prompt contract
