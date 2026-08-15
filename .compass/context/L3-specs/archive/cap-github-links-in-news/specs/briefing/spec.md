# Briefing — Delta Spec

## ADDED Requirements

### Requirement: Distinct Target and Signal Attribution Links

Daily briefing entry title SHALL 链接 saved canonical original target；normalized URL 只用于
identity 与 host classification。每个 contributing source label
SHALL 链接可用的 source-native attribution URL；Hacker News SHALL 优先使用 saved
`metadata.discussion_url`，缺失时 MAY fallback original target。Attribution link choice MUST NOT
改变 dedupe、lane ownership 或 ranking identity。

#### Scenario: Hacker News target and discussion stay distinct

- **WHEN**selected HN signal 的 original target 是 GitHub repository，且 metadata 包含 HN discussion URL
- **THEN**entry title 链接 GitHub repository
- **AND**Signals 下的 `hackernews` label 链接 HN discussion URL

#### Scenario: Historical Hacker News signal lacks discussion URL

- **WHEN**selected historical HN signal 没有 `metadata.discussion_url`
- **THEN**renderer 继续生成可读 attribution
- **AND**source label fallback 到 canonical target，不导致 generation failure

#### Scenario: Non-Hacker-News attribution remains canonical

- **WHEN**selected X 或 WeChat signal 有 canonical source URL
- **THEN**source label 继续链接该 canonical URL
- **AND**HN-specific discussion preference 不改变其他 source attribution

#### Scenario: Dry-run reports only configured maximum

- **WHEN**operator 执行 signals dry-run
- **THEN**preview 展示 configured `github_news_max_items`
- **AND**actual/excluded 标为 unavailable，不显示为 zero observed result

## MODIFIED Requirements

### Requirement: Daily Signal Briefing

Daily discovery SHALL 生成由 `news`、`github` 与 `papers` 三个独立 ranked lane 组成的 quota
briefing。新建/default config SHALL 请求 5 条 verified fresh News、1 条 fresh GitHub 与 1 条
fresh Paper，总计最多 7 条；WeChat MAY 进入 News，但 default 最多 2 条且不是 required quota；
GitHub destination MAY 进入 News，但 default `github_news_max_items=1`。每条 MUST 展示它是什么、
为什么现在值得看、publication/activity source 与 time、contributing link、matched corroboration
与 confidence。Quota artifact MUST 展示 WeChat actual/maximum、News GitHub destination
actual/maximum 与 `excluded_github_news`。Excluded count 只计 greedy selection 为填 quota 实际
遇到且仅因 maximum 跳过的 post-dedupe entry；cross-lane duplicate 与 cutoff 后 candidate 不计。
Dry-run SHALL 只展示 configured maximum，并把 actual/excluded 标为 unavailable，不得伪造 selection
result。

News SHALL 保持 deterministic confidence 与 why-now contract。Dedicated GitHub/Paper entry 没有
independent realtime corroboration 时为 `low`；matching realtime signal SHALL 按同一 one-source /
two-source boundary 提升 confidence。Coverage failure SHALL 单独展示，不得静默改写 confidence。

Signal outcome SHALL 仅在 configured required quota 全部满足且 required source coverage 完整时为
`ready`。有至少一条 entry 时，required quota shortfall、required attempted-source failure 或
unattempted positive-quota source 任一存在都 SHALL 为 `partial`。零 entry 且 required attempted
coverage 完整时为 `no_fresh_signals`；required attempted-source failure 或 unattempted positive-quota
source 存在时为 `coverage_incomplete`。Fresh candidate 全部被 composition maximum 排除时仍按
coverage 完整度使用 zero-entry outcome，但 result copy MUST 说明 exclusion，不得声称没有 fresh
input。Generation crash SHALL 为 `failed`，planning 为 `dry_run`；generic digest/reading-list 为
`legacy`。Status SHALL 同时出现在 Markdown header、serialized DiscoveryReport 与 log summary。

Signals mode 的 source/config state SHALL 遵循：positive GitHub/Paper/legacy WeChat minimum 对应 source
不在 `briefing.sources`、disabled 或没有 configured target 时必须在 network 前 config error；
`news_items>0` 但 `briefing.sources` 内没有 enabled 且有 work 的 realtime source 时同样失败。
`github_news_max_items` 只约束 News composition，MUST NOT 要求 GitHub collector、source membership
或 required coverage。Explicit `--source` 未尝试任何 viable News provider，或漏掉 positive quota
的 required source 时，artifact coverage 不完整。Default optional WeChat source failure SHALL
显示在 coverage；当另一个 attempted viable News source 以 `enabled=true && failed=0` 完成时，
它 MUST NOT 单独降低 outcome。当 WeChat 是唯一 attempted viable News provider 时，其 failure
仍 SHALL 使 coverage incomplete。该 exception 只适用于 quota mode、`wechat_min_items=0` 且
WeChat configured maximum 为 positive 的 run。HN/X 的 attempted selected enabled failure、
positive legacy WeChat minimum failure，以及 legacy `max_items` mode 的任意 attempted realtime
failure SHALL 继续影响 outcome。

Outcome decision table：

| Mode / reports | Nonempty | Empty |
|---|---|---|
| quota mode；HN completed；optional WeChat failed；其他 required coverage 完整 | `ready`（若 quota 满足） | `no_fresh_signals` |
| quota mode；only WeChat attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；HN completed；optional WeChat failed；X attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；positive WeChat minimum and WeChat failed | `partial` | `coverage_incomplete` |
| quota mode；fresh candidate 全被 GitHub destination cap 排除；coverage 完整 | — | `no_fresh_signals` + composition-exclusion copy |
| legacy `max_items`；任一 attempted realtime source failed | `partial` | `coverage_incomplete` |

#### Scenario: Default daily composition is complete

- **WHEN**freshness window 包含至少 5 条满足所有 configured composition cap 的 ranked News、1 条 eligible GitHub 与 1 条 eligible Paper
- **THEN**daily artifact 按 5 News、1 GitHub 与 1 arXiv 分组包含 7 条 entry
- **AND**News MAY 包含最多 2 条 WeChat 与 1 条 GitHub destination；缺少 WeChat 不产生 quota shortfall
- **AND**required source coverage 完整时 status 为 `ready`

#### Scenario: A required lane cannot fill its quota

- **WHEN**至少一条 eligible item 存在，但 fresh GitHub、Paper 或满足 composition cap 的 News candidate 无法填满 configured required quota
- **THEN**artifact 保留全部 eligible entry，并按 required lane 报告 expected、actual 与 missing
- **AND**status 为 `partial`，且 stale、timestamp-unknown、optional WeChat 或 cap-excluded candidate 不得伪造 required coverage

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

完成的 run SHALL 对每个 configured lane 独立应用 freshness。Empty 或 short lane MUST NOT 使用
stale、timestamp-unknown、wrong-lane 或 composition-cap-excluded item 补位。新 signals config
默认 SHALL 使用 `news_items=5`、`wechat_min_items=0`、`wechat_max_items=2`、
`github_news_max_items=1`、`github_items=1`、`paper_items=1`。

New quota field SHALL 为 integer：`news_items` 在 1..10，`wechat_min_items`、
`wechat_max_items` 与 `github_news_max_items` 在 0..news_items，且 WeChat minimum 不得超过
maximum，`github_items` / `paper_items` 在 0..5，总 entry 不得超过 20。Positive dedicated 或
legacy WeChat minimum SHALL 触发 source/target validation；optional WeChat/GitHub destination
maximum 不得单独要求对应 source enabled。Legacy `max_items` 在 1..10 仅当 explicit lane quota
field 均不存在时接受并保持 cap mode。

#### Scenario: No fresh signal is available

- **WHEN**所有 local candidate stale、timestamp-unknown 或 evidence-only，且 required coverage 完整
- **THEN**daily artifact 说明没有 verified fresh signal
- **AND**machine-readable status 为 `no_fresh_signals`

#### Scenario: Fresh signals are excluded by composition maximum

- **WHEN**required coverage 完整、fresh signal 存在、全部被 configured GitHub destination maximum 排除，且没有 eligible dedicated entry
- **THEN**machine-readable status 为 `no_fresh_signals`
- **AND**artifact 说明 fresh candidates 因 composition cap 不 eligible，并展示 excluded count

#### Scenario: Composition exclusion leaves only a dedicated entry

- **WHEN**fresh News 全部被 GitHub destination maximum 排除，但有一个 eligible dedicated entry
- **THEN**artifact 保留 dedicated entry、报告 News missing，status 为 `partial`
- **AND**artifact 展示 composition exclusion count

#### Scenario: No signal and required coverage is incomplete

- **WHEN**没有 verified fresh signal 且至少一个 required source 失败
- **THEN**daily artifact status 是 `coverage_incomplete`，不是 `no_fresh_signals`
- **AND**文案说明 coverage 不完整，因此不能得出 verified empty conclusion

#### Scenario: Keep existing generic briefing modes compatible

- **WHEN**existing config 显式选择 `digest` 或 `reading-list`
- **THEN**existing local-library rendering 保留并标记 `legacy`
- **AND**new signal composition fields 被 ignore；new config 默认 signal mode、`freshness_hours=48` 与 5 News / optional 2 WeChat / maximum 1 GitHub destination / 1 GitHub / 1 Paper composition

#### Scenario: Existing quota config gains default GitHub destination maximum

- **WHEN**existing signals quota config 有 lane fields 但没有 `github_news_max_items`
- **THEN**runtime 使用 default maximum 1
- **AND**不要求 operator migration edit 才能运行

#### Scenario: Legacy positive WeChat minimum stays compatible

- **WHEN**existing quota config 显式设置 positive `wechat_min_items` 而没有 `wechat_max_items`
- **THEN**runtime 保留 required minimum behavior，并允许 WeChat 上限覆盖整个 News lane，同时应用 default GitHub destination maximum 1
- **AND**WeChat minimum shortfall 与 source failure 继续影响 outcome

#### Scenario: Legacy max-items config stays backward compatible

- **WHEN** existing signals config 只有 `max_items: 5`，没有 explicit lane quota field
- **THEN**runtime 将其解释为最多 5 条 uncapped-by-destination News、且 WeChat/GitHub/Paper minimum 为 0
- **AND**complete attempted coverage 下只有 1 条 fresh News 仍为 `ready`

#### Scenario: Legacy max-items coverage behavior stays compatible

- **WHEN**legacy `max_items` signals run 中任一 attempted selected enabled realtime source 失败
- **THEN**nonempty result 为 `partial`，zero result 为 `coverage_incomplete`
- **AND**optional WeChat exception 与 GitHub destination maximum 不适用于 legacy cap mode

#### Scenario: Selective run omits every News provider

- **WHEN**new quota mode 要求 News，但 explicit selective run 只尝试 GitHub/Papers，local 仍有 fresh News sidecar
- **THEN**local News MAY 保留显示，但 result 不能为 `ready`
- **AND**nonempty output 为 `partial`，zero output 为 `coverage_incomplete`

#### Scenario: Conflicting or invalid quota fields are rejected

- **WHEN**signals config 混用 `max_items` 与任一 lane quota（包括 `github_news_max_items`）、违反 min/max/news bounds/relations，或 positive required quota 没有 viable source
- **THEN**config validation 一次报告所有 discoverable quota/source problem
- **AND**discovery network action 不开始
