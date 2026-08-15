# Briefing — Delta Spec

## MODIFIED Requirements

### Requirement: Daily Signal Briefing

Daily discovery SHALL 生成由 `news`、`github` 与 `papers` 三个独立 ranked lane 组成的 quota
briefing。新建/default config SHALL 请求 5 条 verified fresh News、1 条 fresh GitHub 与 1 条
fresh Paper，总计最多 7 条；WeChat MAY 进入 News，但 default 最多 2 条且不是 required quota。
每条 MUST 展示它是什么、为什么现在值得看、publication/activity source 与 time、contributing
link、matched corroboration 与 confidence。

News SHALL 保持 deterministic confidence 与 why-now contract。Dedicated GitHub/Paper entry 没有
independent realtime corroboration 时为 `low`；matching realtime signal SHALL 按同一 one-source /
two-source boundary 提升 confidence。Coverage failure SHALL 单独展示，不得静默改写 confidence。

Signal outcome SHALL 仅在 configured required quota 全部满足且 required source coverage 完整时为
`ready`。有至少一条 entry 时，required quota shortfall、required attempted-source failure 或
unattempted positive-quota source 任一存在都 SHALL 为 `partial`。零 entry 且 required attempted
coverage 完整时为 `no_fresh_signals`；required attempted-source failure 或 unattempted positive-quota
source 存在时为 `coverage_incomplete`。Generation crash SHALL 为 `failed`，planning 为 `dry_run`；
generic digest/reading-list 为 `legacy`。Status SHALL 同时出现在 Markdown header、serialized
DiscoveryReport 与 log summary。

Signals mode 的 source/config state SHALL 遵循：positive GitHub/Paper/legacy WeChat minimum 对应
source 不在 `briefing.sources`、disabled 或没有 configured target 时必须在 network 前 config error；
`news_items>0` 但 `briefing.sources` 内没有 enabled 且有 work 的 realtime source 时同样失败。
Explicit `--source` 未尝试任何 viable News provider，或漏掉 positive quota 的 required source 时，
artifact coverage 不完整。Default optional WeChat source failure SHALL 显示在 coverage；当另一个
attempted viable News source 以 `enabled=true && failed=0` 完成时，它 MUST NOT 单独降低 outcome。
当 WeChat 是唯一 attempted viable News provider 时，其 failure 仍 SHALL 使 coverage incomplete。
该 exception 只适用于 quota mode、`wechat_min_items=0` 且 WeChat configured maximum 为 positive
的 run。HN/X 的 attempted selected enabled failure、positive legacy WeChat minimum failure，以及
legacy `max_items` mode 的任意 attempted realtime failure SHALL 继续影响 outcome。

Outcome decision table：

| Mode / reports | Nonempty | Empty |
|---|---|---|
| quota mode；HN completed；optional WeChat failed；其他 required coverage 完整 | `ready`（若 quota 满足） | `no_fresh_signals` |
| quota mode；only WeChat attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；HN completed；optional WeChat failed；X attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；positive WeChat minimum and WeChat failed | `partial` | `coverage_incomplete` |
| legacy `max_items`；任一 attempted realtime source failed | `partial` | `coverage_incomplete` |

#### Scenario: Default daily composition is complete

- **WHEN** freshness window 包含至少 5 条 ranked News、1 条 eligible GitHub 与 1 条 eligible Paper
- **THEN**daily artifact 按 5 News、1 GitHub 与 1 arXiv 分组包含 7 条 entry
- **AND**News MAY 包含最多 2 条 WeChat，缺少 WeChat 不产生 quota shortfall
- **AND**required source coverage 完整时 status 为 `ready`

#### Scenario: A required lane cannot fill its quota

- **WHEN**至少一条 eligible item 存在，但 fresh GitHub、Paper 或 News candidate 无法填满 configured required quota
- **THEN**artifact 保留全部 eligible entry，并按 required lane 报告 expected、actual 与 missing
- **AND**status 为 `partial`，且 stale、timestamp-unknown 或 optional WeChat 不得伪造 required coverage

#### Scenario: Optional WeChat source fails with another completed News source

- **WHEN**default optional WeChat collection 失败，但另一个 attempted viable News source 完成且 required quota 满足
- **THEN**source coverage 保留 WeChat failure detail 并标记它是 optional
- **AND**该 failure 不单独把 outcome 从 `ready` 降为 `partial`

#### Scenario: Optional WeChat is the only attempted News provider

- **WHEN**selective run 只尝试 WeChat 作为 News provider 且 collection 失败
- **THEN**nonempty output 为 `partial`，zero output 为 `coverage_incomplete`
- **AND**不得把结果解释为 verified quiet day

#### Scenario: Optional WeChat fails during a completed empty News sweep

- **WHEN**HN 是 attempted viable News source 且 `enabled=true, failed=0`，optional WeChat 失败，所有 candidate 都不 fresh
- **THEN**zero-entry result 为 `no_fresh_signals`
- **AND**artifact 仍展示 optional WeChat failure，但不把它解释为 required coverage gap

#### Scenario: Another attempted News source still fails

- **WHEN**HN 完成、optional WeChat 失败，且 enabled X 也 attempted and failed
- **THEN**nonempty result 为 `partial`，zero result 为 `coverage_incomplete`
- **AND**只有 WeChat failure 被 optional exception 忽略，X failure 继续影响 outcome

#### Scenario: Corroboration changes confidence and why-now reasons

- **WHEN** dedicated GitHub/Paper entry 或 News item 有 matching independent realtime signal
- **THEN**confidence 反映实际 corroborating source 数量与类型
- **AND**why-now 列出 lane、timestamp field、age band 与 corroboration reason

### Requirement: Honest Empty Signal Result

完成的 run SHALL 对每个 configured lane 独立应用 freshness。Empty 或 short required lane MUST NOT
使用 stale、timestamp-unknown 或 wrong-lane item 补位。新 signals config 默认 SHALL 使用
`news_items=5`、`wechat_min_items=0`、`wechat_max_items=2`、`github_items=1`、`paper_items=1`。

New quota field SHALL 为 integer：`news_items` 在 1..10，`wechat_min_items` 与
`wechat_max_items` 在 0..news_items 且 minimum 不得超过 maximum，`github_items` /
`paper_items` 在 0..5，总 entry 不得超过 20。Positive dedicated 或 legacy WeChat minimum SHALL
触发 source/target validation；optional WeChat maximum 不得单独要求 source enabled。Legacy
`max_items` 在 1..10 仅当 explicit lane quota field 均不存在时接受并保持 cap mode。

#### Scenario: No fresh signal is available

- **WHEN**所有 local candidate stale、timestamp-unknown 或 evidence-only，且 required coverage 完整
- **THEN**daily artifact 说明没有 verified fresh signal
- **AND**machine-readable status 为 `no_fresh_signals`

#### Scenario: No signal and required coverage is incomplete

- **WHEN**没有 verified fresh signal 且至少一个 required source 失败
- **THEN**daily artifact status 是 `coverage_incomplete`，不是 `no_fresh_signals`
- **AND**文案说明 coverage 不完整，因此不能得出 verified empty conclusion

#### Scenario: Keep existing generic briefing modes compatible

- **WHEN**existing config 显式选择 `digest` 或 `reading-list`
- **THEN**existing local-library rendering 保留并标记 `legacy`
- **AND**new config 默认 signal mode、`freshness_hours=48` 与 5 News / optional 2 WeChat / 1 GitHub / 1 Paper composition

#### Scenario: Legacy positive WeChat minimum stays compatible

- **WHEN**existing quota config 显式设置 positive `wechat_min_items` 而没有 `wechat_max_items`
- **THEN**runtime 保留 required minimum behavior，并允许 WeChat 上限覆盖整个 News lane
- **AND**WeChat minimum shortfall 与 source failure 继续影响 outcome

#### Scenario: Legacy max-items coverage behavior stays compatible

- **WHEN**legacy `max_items` signals run 中任一 attempted selected enabled realtime source 失败
- **THEN**nonempty result 为 `partial`，zero result 为 `coverage_incomplete`
- **AND**optional WeChat exception 不适用于 legacy cap mode

#### Scenario: Conflicting or invalid quota fields are rejected

- **WHEN**signals config 混用 `max_items` 与 lane quota、违反 min/max/news bounds/relations，或 positive required quota 没有 viable source
- **THEN**config validation 一次报告所有 discoverable quota/source problem
- **AND**discovery network action 不开始
