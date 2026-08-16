# Briefing — Delta Spec

## MODIFIED Requirements

### Requirement: Distinct Target and Signal Attribution Links

Daily briefing entry title SHALL 链接 saved canonical original target；normalized URL 只用于
identity。每个 contributing source label SHALL 链接可用的 source-native attribution URL；
Hacker News SHALL 优先使用 saved `metadata.discussion_url`，缺失时 MAY fallback original
target。Attribution link choice MUST NOT 改变 dedupe、source ownership 或 ranking identity。

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

#### Scenario: Dry-run reports configured source maxima

- **WHEN**operator 执行 signals dry-run
- **THEN**preview 展示 configured `hackernews_items`、WeChat optional maximum、`x_items`、
  `github_items` 与 `paper_items`
- **AND**不展示 GitHub destination actual/excluded，也不把 dry-run 标成已执行 selection

### Requirement: Daily Signal Briefing

Daily discovery SHALL 生成按 collect `source` 分组的 quota briefing：`papers`、`github`、
`hackernews`、`wechat` 与 `x`。新建/default config SHALL 请求 3 条 verified fresh Hacker News、
最多 2 条 optional WeChat、0 条 X、1 条 fresh GitHub 与 1 条 fresh Paper；WeChat 缺少不形成
required shortfall。`news` 不得作为用户可见 grouping 或 quota 名。GitHub collector evidence
只 MAY 进入 GitHub section；HN/X/WeChat signal 即使 canonical target 指向 github.com 也 SHALL
进入其自身 source section。

每条 MUST 展示它是什么、为什么现在值得看、publication/activity source 与 time、contributing
link、matched corroboration 与 confidence。Quota artifact MUST 按 required source 展示
expected / actual / missing，并展示 WeChat actual / optional maximum。`x_items=0` 时 MUST NOT
渲染 X section。Dry-run SHALL 只展示 configured source maxima，不得伪造 selection result。

Realtime 与 dedicated entry SHALL 保持 deterministic confidence 与 why-now contract。Dedicated
GitHub/Paper entry 没有 independent realtime corroboration 时为 `low`；matching realtime
signal SHALL 按同一 one-source / two-source boundary 提升 confidence。Coverage failure SHALL
单独展示，不得静默改写 confidence。Why-now 列出 source、timestamp field、age band 与
corroboration reason。

Signal outcome SHALL 仅在 configured required source quota 全部满足且 required source
coverage 完整时为 `ready`。有至少一条 entry 时，required quota shortfall、required
attempted-source failure 或 unattempted positive-quota source 任一存在都 SHALL 为 `partial`。
零 entry 且 required attempted coverage 完整时为 `no_fresh_signals`；required
attempted-source failure 或 unattempted positive-quota source 存在时为
`coverage_incomplete`。Generation crash SHALL 为 `failed`，planning 为 `dry_run`；generic
digest/reading-list 为 `legacy`。Status SHALL 同时出现在 Markdown header、serialized
DiscoveryReport 与 log summary。

Signals mode 的 source/config state SHALL 遵循：positive GitHub/Paper/Hacker News/X/legacy
WeChat minimum 对应 source 不在 `briefing.sources`、disabled 或没有 configured target 时必须
在 network 前 config error。optional WeChat maximum 不得单独要求 WeChat enabled。
Explicit `--source` 漏掉 positive quota 的 required source 时，artifact coverage 不完整。
Default optional WeChat source failure SHALL 显示在 coverage；当另一个 attempted required
realtime source 以 `enabled=true && failed=0` 完成时，它 MUST NOT 单独降低 outcome。
当 WeChat 是唯一 attempted viable realtime provider 时，其 failure 仍 SHALL 使 coverage
incomplete。该 exception 只适用于 quota mode、`wechat_min_items=0` 且 WeChat configured
maximum 为 positive 的 run。HN/X 的 attempted selected enabled failure、positive legacy
WeChat minimum failure，以及 legacy `max_items` mode 的任意 attempted realtime failure
SHALL 继续影响 outcome。

Outcome decision table：

| Mode / reports | Nonempty | Empty |
|---|---|---|
| quota mode；HN completed；optional WeChat failed；其他 required coverage 完整 | `ready`（若 quota 满足） | `no_fresh_signals` |
| quota mode；only WeChat attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；HN completed；optional WeChat failed；X attempted and failed | `partial` | `coverage_incomplete` |
| quota mode；positive WeChat minimum and WeChat failed | `partial` | `coverage_incomplete` |
| legacy `max_items`；任一 attempted realtime source failed | `partial` | `coverage_incomplete` |

#### Scenario: Default daily composition is complete

- **WHEN** freshness window 包含至少 3 条 eligible Hacker News、2 条 eligible WeChat、1 条 eligible GitHub 与 1 条 eligible Paper
- **THEN**daily artifact 按 arXiv、GitHub、Hacker News、WeChat 分组包含 7 条 entry
- **AND**Hacker News MAY 包含指向 github.com 的 story；缺少 WeChat 不产生 quota shortfall
- **AND**required source coverage 完整时 status 为 `ready`

#### Scenario: A required source cannot fill its quota

- **WHEN**至少一条 eligible item 存在，但 fresh GitHub、Paper 或 Hacker News candidate 无法填满 configured required quota
- **THEN**artifact 保留全部 eligible entry，并按 required source 报告 expected、actual 与 missing
- **AND**status 为 `partial`，且 stale、timestamp-unknown 或 optional WeChat 不得伪造 required coverage

#### Scenario: Optional WeChat source fails with another completed realtime source

- **WHEN**default optional WeChat collection 失败，但另一个 attempted required realtime source 完成且 required quota 满足
- **THEN**source coverage 保留 WeChat failure detail 并标记它是 optional
- **AND**该 failure 不单独把 outcome 从 `ready` 降为 `partial`

#### Scenario: Optional WeChat is the only attempted realtime provider

- **WHEN**selective run 只尝试 WeChat 作为 realtime provider 且 collection 失败
- **THEN**nonempty output 为 `partial`，zero output 为 `coverage_incomplete`
- **AND**不得把结果解释为 verified quiet day

#### Scenario: Optional WeChat fails during a completed empty realtime sweep

- **WHEN**HN 是 attempted required realtime source 且 `enabled=true, failed=0`，optional WeChat 失败，所有 candidate 都不 fresh
- **THEN**zero-entry result 为 `no_fresh_signals`
- **AND**artifact 仍展示 optional WeChat failure，但不把它解释为 required coverage gap

#### Scenario: Another attempted realtime source still fails

- **WHEN**HN 完成、optional WeChat 失败，且 enabled X 也 attempted and failed
- **THEN**nonempty result 为 `partial`，zero result 为 `coverage_incomplete`
- **AND**只有 WeChat failure 被 optional exception 忽略，X failure 继续影响 outcome

#### Scenario: Corroboration changes confidence and why-now reasons

- **WHEN** dedicated GitHub/Paper entry 或 realtime source item 有 matching independent realtime signal
- **THEN**confidence 反映实际 corroborating source 数量与类型
- **AND**why-now 列出 source、timestamp field、age band 与 corroboration reason

### Requirement: Honest Empty Signal Result

完成的 run SHALL 对每个 configured source quota 独立应用 freshness。Empty 或 short source
MUST NOT 使用 stale、timestamp-unknown 或 wrong-source item 补位。新 signals config 默认
SHALL 使用 `hackernews_items=3`、`wechat_min_items=0`、`wechat_max_items=2`、`x_items=0`、
`github_items=1`、`paper_items=1`。

New quota field SHALL 为 integer：`hackernews_items` 与 `x_items` 在 0..10，
`wechat_min_items` 与 `wechat_max_items` 在 0..10 且 minimum 不得超过 maximum，
`github_items` / `paper_items` 在 0..5，总 entry
`hackernews_items + wechat_max_items + x_items + github_items + paper_items` 不得超过 20。
Positive dedicated、Hacker News、X 或 legacy WeChat minimum SHALL 触发 source/target
validation；optional WeChat maximum 不得单独要求对应 source enabled。Existing quota config
有 `news_items` 但没有 `hackernews_items` 时 SHALL 迁移 `hackernews_items = news_items`。
Existing `github_news_max_items` MUST 被忽略且不得影响 selection。Legacy `max_items` 在
1..10 仅当 explicit source quota field 均不存在时接受并保持混合 realtime cap mode。

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
- **AND**new config 默认 signal mode、`freshness_hours=48` 与 3 Hacker News / optional 2 WeChat / 1 GitHub / 1 Paper composition

#### Scenario: Existing quota config migrates News pool to Hacker News quota

- **WHEN**existing signals quota config 有 `news_items=5` 与 `wechat_max_items=2` 但没有 `hackernews_items`
- **THEN**runtime 使用 `hackernews_items=5`，WeChat 仍按独立 maximum 2
- **AND**不要求 operator migration edit 才能运行

#### Scenario: Existing GitHub destination maximum is ignored

- **WHEN**existing quota config 仍包含 `github_news_max_items`
- **THEN**validation 成功且 selection 不按 destination host 截断
- **AND**多个 HN GitHub-target story MAY 同时进入 Hacker News section

#### Scenario: Legacy positive WeChat minimum stays compatible

- **WHEN**existing quota config 显式设置 positive `wechat_min_items` 而没有 `wechat_max_items`
- **THEN**runtime 保留 required minimum behavior，并允许 WeChat 上限覆盖其独立 source quota
- **AND**WeChat minimum shortfall 与 source failure 继续影响 outcome

#### Scenario: Legacy max-items config stays backward compatible

- **WHEN** existing signals config 只有 `max_items: 5`，没有 explicit source quota field
- **THEN**runtime 将其解释为最多 5 条混合 realtime entry、且 WeChat/GitHub/Paper/Hacker News/X minimum 为 0
- **AND**complete attempted coverage 下只有 1 条 fresh realtime entry 仍为 `ready`

#### Scenario: Legacy max-items coverage behavior stays compatible

- **WHEN**legacy `max_items` signals run 中任一 attempted selected enabled realtime source 失败
- **THEN**nonempty result 为 `partial`，zero result 为 `coverage_incomplete`
- **AND**optional WeChat exception 与 per-source quota 不适用于 legacy cap mode

#### Scenario: Selective run omits a required source

- **WHEN**new quota mode 要求 Hacker News，但 explicit selective run 只尝试 GitHub/Papers，local 仍有 fresh HN sidecar
- **THEN**local HN MAY 保留显示，但 result 不能为 `ready`
- **AND**nonempty output 为 `partial`，zero output 为 `coverage_incomplete`

#### Scenario: Conflicting or invalid quota fields are rejected

- **WHEN**signals config 混用 `max_items` 与任一 source quota、违反 min/max/total bounds/relations，或 positive required quota 没有 viable source
- **THEN**config validation 一次报告所有 discoverable quota/source problem
- **AND**discovery network action 不开始

## REMOVED Requirements

无。Destination-cap 相关 Scenario 已从上述 MODIFIED Requirement 删除，不再作为 briefing 合同。
