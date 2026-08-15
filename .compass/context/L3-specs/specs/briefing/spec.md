# Briefing Specification

## Purpose

从 local Library 生成适合 Obsidian 阅读的 digest 或 reading list，不重新抓取远端来源。

## Requirements

### Requirement: Local Briefing Input

briefing SHALL 只消费本地 ResearchItem query result。

#### Scenario: Generate from local archive

- **WHEN** operator 生成 briefing
- **THEN**输入来自指定 `output_root` 的 sidecar
- **AND**不会触发 GitHub、arXiv 或 WeChat fetch

### Requirement: Digest and Reading List Modes

briefing SHALL 支持 digest 和 reading-list 两种派生阅读 artifact。

#### Scenario: Select a mode

- **WHEN** operator 选择 digest 或 reading-list
- **THEN**系统生成对应结构的 Markdown
- **AND**保留 item source link 与必要 metadata

### Requirement: Derived Output Boundary

保存的 briefing MUST 写入 `output/briefing/`，不得覆盖 source archive。

#### Scenario: Save briefing

- **WHEN** briefing save 成功
- **THEN**文件写入 digest 或 reading-list 的派生目录
- **AND**`output/github|papers|wechat` 中的 raw artifact 不被修改

### Requirement: Explicit Source Gaps

缺失请求来源或无匹配 item 时，briefing MAY 继续生成，但 MUST 解释 coverage gap。

#### Scenario: Requested source has no items

- **WHEN**其他来源有结果但某个请求来源为空
- **THEN**生成的 briefing 保留成功内容
- **AND**明确标记缺失来源

### Requirement: Preview and Listing

operator SHALL 能在写文件前 preview briefing，并能只读列出已有 briefing。

#### Scenario: Preview without saving

- **WHEN** operator 请求 preview
- **THEN**系统返回派生 Markdown content
- **AND**不会创建 briefing file

### Requirement: Daily Signal Briefing

Daily discovery SHALL 生成由 `news`、`github` 与 `papers` 三个独立 ranked lane 组成的 quota
briefing。新建/default config SHALL 请求 5 条 verified fresh News（其中至少 2 条 WeChat）、
1 条 fresh GitHub 与 1 条 fresh Paper，总计最多 7 条。每条 MUST 展示它是什么、为什么现在值得看、
publication/activity source 与 time、contributing link、matched corroboration 与 confidence。

News SHALL 保持 deterministic confidence 与 why-now contract。Dedicated GitHub/Paper entry 没有
independent realtime corroboration 时为 `low`；matching realtime signal SHALL 按同一 one-source /
two-source boundary 提升 confidence。Coverage failure SHALL 单独展示，不得静默改写 confidence。

Signal outcome SHALL 仅在 configured quota 全部满足且 source coverage 完整时为 `ready`。有至少
一条 entry 时，quota shortfall、attempted-source failure 或 unattempted positive-quota source
任一存在都 SHALL 为 `partial`。零 entry 且 attempted coverage 完整时为 `no_fresh_signals`；
attempted-source failure 或 unattempted positive-quota source 存在时为 `coverage_incomplete`。
Generation crash SHALL 为 `failed`，planning 为 `dry_run`；generic digest/reading-list 为 `legacy`。
Status SHALL 同时出现在 Markdown header、serialized DiscoveryReport 与 log summary。

Signals mode 的 source/config state SHALL 遵循：positive GitHub/Paper/WeChat quota 对应 source
不在 `briefing.sources`、disabled 或没有 configured target 时必须在 network 前 config error；
`news_items>0` 但 `briefing.sources` 内没有 enabled 且有 work 的 realtime source 时同样失败。
Explicit `--source` 未尝试任何 viable News provider，或漏掉 positive quota 的 required source 时，
artifact coverage 不完整；required source 成功但 fresh item 不足只形成 quota shortfall。任意本次
attempted selected enabled source failure 都 SHALL 使 coverage incomplete。Zero-quota source disabled
或未 selected 时不属于 required coverage。

#### Scenario: Default daily composition is complete

- **WHEN** freshness window 包含至少 5 条 ranked News、1 条 eligible GitHub 与 1 条 eligible Paper
- **THEN**daily artifact 按 5 News、1 GitHub 与 1 arXiv 分组包含 7 条 entry
- **AND**5 条 News 中至少 2 条来自 WeChat
- **AND**attempted source coverage 完整时 status 为 `ready`

#### Scenario: A required lane cannot fill its quota

- **WHEN**至少一条 eligible item 存在，但 fresh GitHub、Paper 或 News candidate 无法填满 configured quota
- **THEN**artifact 保留全部 eligible entry，并按 lane 报告 expected、actual 与 missing
- **AND**status 为 `partial`，且 stale、timestamp-unknown 或其他 lane item 不得补位

#### Scenario: Corroboration changes confidence and why-now reasons

- **WHEN** dedicated GitHub/Paper entry 或 News item 有 matching independent realtime signal
- **THEN**confidence 反映实际 corroborating source 数量与类型
- **AND**why-now 列出 lane、timestamp field、age band 与 corroboration reason

### Requirement: Honest Empty Signal Result

完成的 run SHALL 对每个 configured lane 独立应用 freshness。Empty 或 short lane MUST NOT 使用
stale、timestamp-unknown 或 wrong-lane item 补位。新 signals config 默认 SHALL 使用
`news_items=5`、`wechat_min_items=2`、`github_items=1`、`paper_items=1`。

新 quota field SHALL 为 integer：`news_items` 在 1..10，`wechat_min_items` 在
0..news_items，`github_items` / `paper_items` 在 0..5，总 entry 不得超过 20。Positive dedicated
或 WeChat quota SHALL 触发 Daily Signal Briefing 的 source/target validation。Legacy
`max_items` 在 1..10 仅当四个新 quota field 均不存在时接受，并保持 cap mode：最多选择
`max_items` 条 News，dedicated/WeChat minimum 为 0；不足 cap 的 nonempty result 不得因此
变成 `partial`。Explicit digest/reading-list mode 忽略 signal quota composition 并保持 legacy behavior。

#### Scenario: No fresh signal is available

- **WHEN**所有 local candidate stale、timestamp-unknown 或 evidence-only
- **THEN**daily artifact 说明没有 verified fresh signal
- **AND**machine-readable status 为 `no_fresh_signals`

#### Scenario: No signal and coverage is incomplete

- **WHEN**没有 verified fresh signal 且至少一个 configured realtime source 失败
- **THEN**daily artifact status 是 `coverage_incomplete`，不是 `no_fresh_signals`
- **AND**文案说明 coverage 不完整，因此不能得出 verified empty conclusion

#### Scenario: Keep existing generic briefing modes compatible

- **WHEN**existing config 显式选择 `digest` 或 `reading-list`
- **THEN**existing local-library rendering 保留并标记 `legacy`
- **AND**new config 默认 signal mode，`freshness_hours=48`（最大 72）与 5/2/1/1 composition

#### Scenario: Legacy max-items config stays backward compatible

- **WHEN** existing signals config 只有 `max_items: 5`，没有 explicit lane quota field
- **THEN**runtime 将其解释为最多 5 条 News、且 WeChat/GitHub/Paper minimum 为 0
- **AND**complete attempted coverage 下只有 1 条 fresh News 仍为 `ready`

#### Scenario: Selective run omits every News provider

- **WHEN**new quota mode 要求 News，但 explicit selective run 只尝试 GitHub/Papers，local 仍有 fresh News sidecar
- **THEN**local News MAY 保留显示，但 result 不能为 `ready`
- **AND**nonempty output 为 `partial`，zero output 为 `coverage_incomplete`

#### Scenario: Conflicting or invalid quota fields are rejected

- **WHEN**signals config 混用 `max_items` 与新 quota、违反 bounds/relations，或 positive quota 没有 viable source
- **THEN**config validation 一次报告所有 discoverable quota/source problem
- **AND**discovery network action 不开始

### Requirement: Source Coverage in Daily Briefing

Daily signal briefing SHALL 独立展示 configured source coverage 与 content ranking，使 blocked
WeChat 或 X source 不被误报为 quiet day。

#### Scenario: One realtime source fails

- **WHEN**一个 configured realtime source 失败，另一个产生 usable signal
- **THEN**briefing 保留并排名成功 signal
- **AND**failed source 与 reason 出现在 coverage note
