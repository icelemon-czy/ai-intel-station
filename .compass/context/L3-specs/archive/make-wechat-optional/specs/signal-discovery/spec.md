# Signal Discovery — Delta Spec

## MODIFIED Requirements

### Requirement: Explicit Signal and Evidence Roles

每个 candidate SHALL 保留 source role。WeChat/Hacker News/X 是 realtime `signal`，只 MAY 进入
`news` lane。GitHub repository/search 与 Papers 是 `evidence`，MUST NOT 填充 News quota，但
verified fresh evidence MAY 在各自 `github` / `papers` dedicated lane 成为 primary reading item。
跨 lane exact normalized URL/title SHALL 只显示一次，ownership precedence 为
`papers > github > news`。

Default News mix SHALL 把 WeChat 作为 optional contribution，按 deduplicated rendered News entry
最多选择 `wechat_max_items=2`；缺少 WeChat 不形成 quota shortfall。Explicit legacy
`wechat_min_items>0` SHALL 先 reserve minimum，再在 configured maximum 内填充。一个 entry 只要
包含至少一个 WeChat contribution 就计一个 WeChat slot；多个 raw WeChat 合并后只计一个，作为
dedicated corroboration 的 WeChat 不占 News slot。

#### Scenario: Evidence enters only its dedicated lane

- **WHEN** fresh GitHub 与 Paper evidence 存在，但没有 realtime News signal
- **THEN**两者只 MAY 占据各自 dedicated lane
- **AND**均不计入 5 条 News quota

#### Scenario: Exact cross-lane duplicate has one owner

- **WHEN** HN/X/WeChat signal 与 selected GitHub/Paper item 共享 normalized URL 或 exact normalized title
- **THEN**artifact 只显示一个 dedicated-lane entry，不显示第二个 News entry
- **AND**realtime contribution 提升 corroboration，News lane 使用另一 eligible candidate 或报告 shortfall

#### Scenario: Paper and GitHub candidates are exact duplicates

- **WHEN** selected Paper 与 GitHub candidate 共享 normalized URL 或 exact normalized title
- **THEN**Paper lane 拥有 entry，GitHub lane 选择下一 distinct eligible candidate
- **AND**没有 replacement 时 GitHub 报告 shortfall，status 不得为 `ready`

#### Scenario: Default News mix caps optional WeChat

- **WHEN**ranked News pool 有超过 2 个 deduped WeChat entry 和足够 non-WeChat candidate
- **THEN**default News lane 最多包含 2 个 WeChat entry
- **AND**其余位置按 deterministic rank 用 non-WeChat candidate 填充

#### Scenario: Default News mix has no WeChat

- **WHEN**没有 eligible WeChat entry，但有足够 HN/X candidate
- **THEN**HN/X MAY 填满 5 条 News
- **AND**缺少 WeChat 不形成 missing quota 或 `partial`

#### Scenario: Optional WeChat cap can leave News short

- **WHEN**`news_items=5`、`wechat_min_items=0`、`wechat_max_items=2`，且 pool 只有 5 个 deduped WeChat entry
- **THEN**News lane 只选择 2 个 WeChat entry，不绕过 maximum
- **AND**News missing=3，nonempty briefing outcome 为 `partial`

#### Scenario: Legacy WeChat minimum remains required

- **WHEN**config 显式设置 positive legacy WeChat minimum 且 eligible WeChat 少于 minimum
- **THEN**其他 signal MAY 填满 News lane
- **AND**missing minimum 继续形成 quota shortfall

#### Scenario: Duplicate WeChat signals consume one optional slot

- **WHEN**两个 raw WeChat candidate normalize 为一个 News entry，另一 mixed WeChat/HN group normalize 为第二个
- **THEN**两个 rendered News entry 共占 2 个 WeChat slot
- **AND**raw candidate count 不得提前耗尽或绕过 maximum
