# Signal Discovery — Delta Spec

## ADDED Requirements

### Requirement: GitHub Destination Cap in News

Quota-mode signal discovery SHALL 在 cross-lane exact dedupe 后，对 deduplicated rendered News
entry 应用 configurable `github_news_max_items`。Normalized destination host 为 `github.com` 或
其 subdomain 的 entry 计入 cap；`github.io` hosting domain 不计入。Default SHALL 为 1，config
MUST 是 `0..news_items` 的 integer。超过 cap 的 candidate MUST 使用后续 eligible non-GitHub
candidate replacement；没有 replacement 时 MUST 报告 News shortfall，不得绕过 cap。Legacy
`max_items` mode SHALL 保持既有 uncapped behavior。Existing quota config 缺 field SHALL 使用
default 1；`max_items` 与 explicit `github_news_max_items` 混用 MUST 为 config error；generic
digest/reading-list SHALL ignore 该 field。Positive maximum MUST NOT 要求 GitHub collector enabled、
加入 `briefing.sources` 或成为 required coverage。

一个 deduped entry 同时包含 WeChat contribution 且 destination 为 GitHub 时 SHALL 同时消耗
WeChat 与 GitHub slot。GitHub maximum MUST NOT 被 positive WeChat minimum reservation 绕过；
maximum 冲突 SHALL 保留 eligible subset并报告 WeChat minimum shortfall；只有 replacement 不足时
同时报告 News shortfall。
`excluded_github_news` SHALL 只计 post-cross-lane-dedupe greedy selection 为填 News quota 实际
遇到且仅因 GitHub maximum 跳过的 deduped entry；dedicated corroboration duplicate 与 selection
已填满后未访问的 lower-ranked candidate MUST NOT 计入。

#### Scenario: Higher-ranked GitHub links are capped and replaced

- **WHEN**ranked News pool 有超过 default cap 的 GitHub destination entry，并有足够较低排名的 non-GitHub candidate
- **THEN**News 最多选择 1 条 GitHub destination entry
- **AND**其余位置按既有 deterministic rank 使用 non-GitHub replacement 填满

#### Scenario: GitHub cap can leave News short

- **WHEN**ranked News pool 的 GitHub destination 超过 cap，且 non-GitHub replacement 不足
- **THEN**selector 不绕过 cap
- **AND**artifact 报告实际 News missing，nonempty outcome 为 `partial`

#### Scenario: Dedicated duplicate does not consume News GitHub cap

- **WHEN**一个 HN GitHub destination 与 selected dedicated GitHub entry exact match，另有一个 distinct HN GitHub destination
- **THEN**exact match 只作为 dedicated corroboration，不显示为 News entry
- **AND**distinct HN GitHub destination仍可使用一个 News GitHub slot

#### Scenario: Legacy News cap stays compatible

- **WHEN**signals config 使用 legacy `max_items` 而没有 lane quota fields
- **THEN**existing News selection 不应用 `github_news_max_items`
- **AND**多个 GitHub destination MAY 按既有 rank 进入 legacy output

#### Scenario: Host classification rejects suffix lookalikes

- **WHEN**candidate destinations 分别使用 mixed-case `github.com`、`gist.github.com`、
  `github.io`、`user.github.io`、`notgithub.com` 与 `github.com.evil.example`
- **THEN**只有 `github.com` 与 `gist.github.com` 计入 GitHub destination cap
- **AND**classification 在 URL normalization 后、deduped rendered entry 上执行

#### Scenario: GitHub maximum takes precedence with replacement

- **WHEN**positive WeChat minimum 需要两个 mixed WeChat/GitHub entry、GitHub destination maximum 为 1，且有足够 eligible non-GitHub replacement
- **THEN**selector 最多保留一个 mixed entry，并同时计一个 WeChat slot 与一个 GitHub slot
- **AND**artifact 报告 WeChat minimum shortfall，但 replacement 填满 News、不报告 News shortfall

#### Scenario: GitHub maximum takes precedence without replacement

- **WHEN**positive WeChat minimum 需要两个 mixed WeChat/GitHub entry、GitHub destination maximum 为 1，且没有足够 eligible replacement
- **THEN**selector 最多保留一个 mixed entry，不得由 reservation 绕过 maximum
- **AND**artifact 同时报告 WeChat minimum 与 News shortfall

#### Scenario: Zero GitHub maximum produces honest zero-entry result

- **WHEN**`github_news_max_items=0`、`github_items=0`、`paper_items=0`、coverage 完整且 fresh News pool 只有 GitHub destination
- **THEN**artifact status 为 `no_fresh_signals`
- **AND**result copy 与 composition summary 明示 fresh candidates 被 GitHub destination cap 排除

#### Scenario: Zero GitHub maximum with a dedicated entry is partial

- **WHEN**`github_news_max_items=0`、fresh News pool 只有 GitHub destination，但有一个 eligible dedicated Paper/GitHub entry
- **THEN**artifact 保留 dedicated entry 并报告 News shortfall
- **AND**nonempty status 为 `partial`，不是 `no_fresh_signals`

#### Scenario: Excluded count follows greedy selection

- **WHEN**post-dedupe rank 依次包含 selected GitHub entry、两个 cap-skipped GitHub entry、足够 replacement，以及 selection cutoff 后另一个 GitHub entry
- **THEN**`excluded_github_news=2`
- **AND**cross-lane dedicated duplicate 与 cutoff 后 candidate 均不计入 excluded count

#### Scenario: Maximum does not require GitHub collection

- **WHEN**quota config 设置 positive `github_news_max_items`，但 GitHub collector disabled 且
  dedicated `github_items=0`
- **THEN**config validation 成功，News source 可独立运行
- **AND**GitHub maximum 不进入 required source coverage

## MODIFIED Requirements

### Requirement: Explicit Signal and Evidence Roles

每个 candidate SHALL 保留 source role。WeChat/Hacker News/X 是 realtime `signal`，只 MAY 进入
`news` lane。GitHub repository/search 与 Papers 是 `evidence`，MUST NOT 填充 News quota，但
verified fresh evidence MAY 在各自 `github` / `papers` dedicated lane 成为 primary reading item。
跨 lane exact normalized URL/title SHALL 只显示一次，ownership precedence 为
`papers > github > news`。Owning dedicated entry 保留 matching realtime signal 作为 corroboration；
lower-precedence lane 选择下一 eligible distinct candidate，否则报告 shortfall。

Default News mix SHALL 把 WeChat 作为 optional contribution，按 deduplicated rendered News entry
最多选择 `wechat_max_items=2`；缺少 WeChat 不形成 quota shortfall。Explicit legacy
`wechat_min_items>0` SHALL 先 reserve minimum，但 reservation 仍 MUST 满足所有 configured maximum。
一个 entry 只要包含至少一个 WeChat contribution 就计一个 WeChat slot；多个 raw WeChat 合并后
只计一个，作为 dedicated corroboration 的 WeChat 不占 News slot。Quota-mode News SHALL 同时按
deduplicated rendered entry 应用 `github_news_max_items`，default 为 1；mixed WeChat/GitHub entry
同时消耗两个 slot。

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

- **WHEN**ranked News pool 有超过 2 个 deduped WeChat entry 和足够满足所有 configured composition cap 的 replacement candidate
- **THEN**default News lane 最多包含 2 个 WeChat entry
- **AND**其余位置按 deterministic rank 使用 eligible replacement 填充

#### Scenario: Default News mix has no WeChat

- **WHEN**没有 eligible WeChat entry，但有足够满足所有 configured composition cap 的 HN/X candidate
- **THEN**HN/X MAY 填满 5 条 News
- **AND**缺少 WeChat 不形成 missing quota 或 `partial`

#### Scenario: Optional WeChat cap can leave News short

- **WHEN**`news_items=5`、`wechat_min_items=0`、`wechat_max_items=2`，且 pool 只有 5 个 deduped WeChat entry
- **THEN**News lane 只选择 2 个 WeChat entry，不绕过 maximum
- **AND**News missing=3，nonempty briefing outcome 为 `partial`

#### Scenario: Legacy WeChat minimum remains required

- **WHEN**config 显式设置 positive legacy WeChat minimum 且 eligible WeChat 少于 minimum
- **THEN**其他满足 configured maximum 的 signal MAY 填满 News lane
- **AND**missing minimum 继续形成 quota shortfall

#### Scenario: Duplicate WeChat signals consume one optional slot

- **WHEN**两个 raw WeChat candidate normalize 为一个 News entry，另一 mixed WeChat/HN group normalize 为第二个
- **THEN**两个 rendered News entry 共占 2 个 WeChat slot
- **AND**raw candidate count 不得提前耗尽或绕过任何 configured maximum
