# Daily Discovery — Delta Spec

## MODIFIED Requirements

### Requirement: Config Initialization and Validation

operator SHALL 能从 bundled example 创建 discovery config；无效 config MUST 一次报告所有可发现
validation problem。Newly initialized signals config SHALL 对 default quota internally viable：启用并
配置 Hacker News target、GitHub target 与 Paper category。Default WeChat watchlist MAY
保持启用以提供最多 2 条 optional WeChat，但不得成为 config validity 或 `ready` 的前置条件。
Signals config SHALL 在 network 前验证 quota bounds/relations 与 positive required quota source
membership、enabled state 和 target availability。

#### Scenario: Initialize first-run config

- **WHEN** operator 运行 `research init-config`
- **THEN**系统从 example 写入目标 YAML
- **AND**默认不覆盖已有文件，除非 operator 明确 force

#### Scenario: Initialize a viable quota config

- **WHEN** operator 运行 `research init-config`
- **THEN**generated YAML 包含 3 Hacker News / optional maximum 2 WeChat / 1 GitHub / 1 Paper composition
- **AND**network-free dry-run 验证最多 7-item composition

#### Scenario: Positive required quota has no viable source

- **WHEN**signals config 要求的 required source 不在 `briefing.sources`、disabled 或没有 configured work
- **THEN**validation 在 collection 前一次报告所有 discoverable source/quota problem
- **AND**optional WeChat maximum 不单独触发 validation failure

### Requirement: Agent-Operated Daily Intelligence

project-local daily intelligence Skill SHALL 把自然语言 intent 转换为现有 `research` action，
执行它、读取 local quota-composed artifact，并按 arXiv、GitHub、Hacker News、WeChat 与（若
`x_items>0`）X 分组返回不超过 configured source total（default 最多 7）的 verified fresh
item，以及 required source coverage 与 quota shortfall。Normal flow MUST NOT 把 missing
required source 表示为 complete daily briefing，也不得要求 user 自己编辑 YAML、读取 log、
启动 Web 或编排 CLI。Agent MUST NOT 把 HN GitHub-target story 报告为 GitHub news，也不得
再报告 GitHub destination excluded count。

#### Scenario: Ask what is worth reading today

- **WHEN** user 询问今天有什么值得关注，且没有明确要求 rerun
- **THEN**Agent 先只读检查今日 discovery 与 briefing status
- **AND**今日 `ready`、`partial`、`no_fresh_signals` 或 `coverage_incomplete` 的 non-dry-run signal artifact 不被立即自动重跑
- **AND**dry-run、failed、stale 或 legacy empty artifact 不得伪装成今日 signal result

#### Scenario: Return the default grouped composition

- **WHEN** user 询问今天有什么值得看，且 usable quota-composed artifact 存在
- **THEN**Agent 在 default config 下返回最多 1 条 arXiv、1 条 GitHub、3 条 Hacker News 与 2 条 optional WeChat
- **AND**没有 WeChat 时不把它报告为 required shortfall
- **AND**每条说明它是什么与为什么现在值得看

#### Scenario: Return a partial-success briefing

- **WHEN**今日 run 有成功 signal source 且一个或多个 source 失败
- **THEN**Agent 返回成功的 ranked item
- **AND**单独报告 succeeded、skipped 与 failed source coverage

#### Scenario: Existing Codex daily automation follows the current composition

- **WHEN**Codex automation `ai` 在每日 09:00 触发
- **THEN**prompt 要求读取或生成按 source 分组的最多 7 条 briefing，并使用 optional maximum 2 WeChat 语义
- **AND**保留 target task、schedule、真实 artifact 与 honest partial-failure 约束
- **AND**update 后 read-back 验证 task id/target、09:00 recurrence 与完整 prompt contract

#### Scenario: Return a partial quota briefing

- **WHEN**今日 artifact 有 eligible item，但一个或多个 required source quota 未填满
- **THEN**Agent 按 source 返回成功 item
- **AND**单独报告 missing source count 与 succeeded/skipped/failed source coverage

#### Scenario: Today's result has incomplete coverage and no Top items

- **WHEN**今日真实 artifact status 是 `coverage_incomplete`
- **THEN**Agent 说明因 coverage 不完整而没有可验证的新结果，而不是称为 quiet day
- **AND**Agent 报告 failed source，并等待明确 rerun intent 或后续 schedule，不立即重复相同 network attempt

#### Scenario: Set up a first daily sweep

- **WHEN** user 请求首次运行或调整明确的 discovery preference
- **THEN**Agent 创建或最小修改 ignored config，并执行 network-free dry-run validation
- **AND**normal flow 不要求 user 自己编辑 YAML
- **AND**只有 user 明确请求自动 schedule 时才修改本机 scheduler
