# Signal Discovery Specification

## Purpose

从 realtime social source 收集可验证的 fresh signal，并用 local evidence 做 deterministic
dedupe、corroboration 与 ranking，为 daily briefing 提供事实输入。

## Requirements

### Requirement: Realtime Signal Sources

signal discovery SHALL 支持 independently configured Hacker News public feed 与 X recent search；
disabled 或 unavailable source MUST NOT 阻止其他 source 完成。

#### Scenario: Collect Hacker News signals

- **WHEN** Hacker News 启用并配置 feed 与 keyword preference
- **THEN**系统拉取 recent matching story 并保存 normalized ResearchItem sidecar
- **AND**每条保存 publication time、discussion link 与可用 score/comment metric

#### Scenario: Hacker News returns malformed or unavailable data

- **WHEN** Hacker News feed/item response unavailable、malformed 或超出 bounded response limit
- **THEN**source 以 affected feed/item context 报告 failure
- **AND**不把 malformed response 保存为空成功

#### Scenario: Collect X recent-search signals

- **WHEN** X 启用、配置有效 token environment variable 与至少一个 query
- **THEN**系统请求带 creation time、author、public metric 的 recent Post 并保存 normalized signal sidecar
- **AND**request 受 per-query limit 与 `briefing.freshness_hours` 对应的显式 `start_time/end_time` 约束

#### Scenario: X credential is unavailable

- **WHEN** X 启用但 configured bearer-token environment variable 缺失
- **THEN**X 在不发 request 的情况下报告 actionable failure
- **AND**其他 independent source 与 briefing stage 继续

### Requirement: Explicit Signal and Evidence Roles

每个 candidate SHALL 保留 source role。WeChat/Hacker News/X 是 realtime `signal`，只 MAY
进入各自 source section。GitHub repository/search 与 Papers 是 `evidence`，MUST NOT 填充
Hacker News / WeChat / X quota，但 verified fresh evidence MAY 在各自 `github` / `papers`
section 成为 primary reading item。跨 source exact normalized URL/title SHALL 只显示一次，
ownership precedence 为 `papers > github > hackernews > wechat > x`。Owning entry 保留
matching lower-precedence realtime signal 作为 corroboration；lower-precedence source
选择下一 eligible distinct candidate，否则报告该 source shortfall。

Default mix SHALL 把 WeChat 作为独立 optional source，最多选择 `wechat_max_items=2`；
缺少 WeChat 不形成 quota shortfall。Explicit legacy `wechat_min_items>0` SHALL 要求
WeChat-owned entry 达到 minimum。一个 WeChat-owned rendered entry 计一个 WeChat slot；
作为 dedicated 或 HN/X corroboration 的 WeChat 不占 WeChat quota。Hacker News SHALL 独立
选择最多 `hackernews_items` 条，default 3；canonical target 是否为 github.com MUST NOT
改变其 source 归属。

#### Scenario: Evidence enters only its dedicated source

- **WHEN** fresh GitHub 与 Paper evidence 存在，但没有 realtime signal
- **THEN**两者只 MAY 占据各自 source section
- **AND**均不计入 Hacker News 或 WeChat quota

#### Scenario: Exact cross-source duplicate has one owner

- **WHEN** HN/X/WeChat signal 与 selected GitHub/Paper item 共享 normalized URL 或 exact normalized title
- **THEN**artifact 只显示一个 dedicated source entry，不显示第二个 realtime entry
- **AND**realtime contribution 提升 corroboration，被拥有 source 使用另一 eligible candidate 或报告 shortfall

#### Scenario: Paper and GitHub candidates are exact duplicates

- **WHEN** selected Paper 与 GitHub candidate 共享 normalized URL 或 exact normalized title
- **THEN**Paper section 拥有 entry，GitHub section 选择下一 distinct eligible candidate
- **AND**没有 replacement 时 GitHub 报告 shortfall，status 不得为 `ready`

#### Scenario: Default WeChat mix caps optional WeChat

- **WHEN**ranked WeChat pool 有超过 2 个 deduped WeChat entry 和足够 Hacker News candidate
- **THEN**WeChat section 最多包含 2 个 entry
- **AND**Hacker News 按其自身 quota 独立填充，不占用 WeChat slot

#### Scenario: Default mix has no WeChat

- **WHEN**没有 eligible WeChat entry，但有足够 Hacker News candidate
- **THEN**Hacker News MAY 填满 `hackernews_items`
- **AND**缺少 WeChat 不形成 missing quota 或 `partial`

#### Scenario: Optional WeChat cap does not steal Hacker News quota

- **WHEN**`hackernews_items=3`、`wechat_min_items=0`、`wechat_max_items=2`，且 pool 只有 5 个 deduped WeChat entry、没有 HN
- **THEN**WeChat section 只选择 2 个 entry，Hacker News actual=0
- **AND**missing 包含 Hacker News，nonempty briefing outcome 为 `partial`

#### Scenario: Legacy WeChat minimum remains required

- **WHEN**config 显式设置 positive legacy WeChat minimum 且 eligible WeChat-owned entry 少于 minimum
- **THEN**其他 source MAY 填满各自 quota
- **AND**missing WeChat minimum 继续形成 quota shortfall

#### Scenario: Duplicate WeChat signals consume one optional slot

- **WHEN**两个 raw WeChat candidate normalize 为一个 WeChat entry
- **THEN**该 rendered entry 占 1 个 WeChat slot
- **AND**raw candidate count 不得提前耗尽或绕过 WeChat maximum

#### Scenario: Hacker News GitHub targets stay in Hacker News

- **WHEN**ranked Hacker News pool 有多条 canonical target 为 github.com 的 fresh story，且没有 matching dedicated GitHub entry
- **THEN**这些 story 按 Hacker News quota 选择
- **AND**selection 不得因 destination host 丢弃或改分到 GitHub section

### Requirement: Verifiable Freshness

News 与 Paper entry MUST 使用 configured freshness window 内可解析的 `published_at`。GitHub entry
MUST 使用可解析的 `updated_at`，缺失时 fallback `published_at`。`discovered_at` 与 filesystem mtime
MUST NOT 替代 source time。Source timestamp SHALL normalize 为 timezone-aware UTC；legacy
timezone-naive WeChat timestamp SHALL 解释为 Asia/Shanghai。Freshness lower boundary inclusive；
未来超过 5 分钟的 timestamp 排除为不可验证 clock skew。

#### Scenario: First observed item has unknown publication time

- **WHEN** item 今日首次观测但没有可解析 `published_at`
- **THEN**它被排除在 verified fresh Top list
- **AND**系统不标记为今日发表

#### Scenario: Timestamp is exactly on or outside the freshness boundary

- **WHEN**一个 signal 恰好在 `freshness_hours` lower boundary，另一个早 1 秒，第三个在未来超过 5 分钟
- **THEN**仅 exact-boundary signal 通过 freshness gate
- **AND**evaluation 使用 configured timezone-aware `now`，不用 filesystem mtime

#### Scenario: Each lane applies its source timestamp

- **WHEN** fresh Paper 有 `published_at`、GitHub repository 有 recent `updated_at`，另一个 evidence item 只有 `discovered_at`
- **THEN**Paper 与 GitHub item eligible 于各自 dedicated lane
- **AND**discovery-only evidence item 作为 unverifiable 被排除

### Requirement: Deterministic Signal Ranking

News ranking SHALL 继续依次优先 24-hour freshness band、configured watchlist、independent
corroboration、source-local engagement percentile、publication time。Engagement percentile SHALL
只在 current run 同 source candidate 内计算（单个 candidate 为 neutral `0.5`）；不同平台 raw
engagement count MUST NOT 直接比较。Papers SHALL 按 publication time，再按 normalized URL/title。
GitHub SHALL 先优先 freshness window 内新创建的 repository，再按 source activity time
（`updated_at` fallback `published_at`）与 stable URL/title。Lifetime stars MUST NOT 超过 fresher creation。

#### Scenario: Watchlist signal competes with lifetime-popular evidence

- **WHEN** fresh watchlist signal 与高 star historical GitHub repository 同时存在
- **THEN**watchlist signal 进入 daily Top list
- **AND**repository 不得填充 News quota；仅在满足 dedicated freshness 时 MAY 进入 GitHub lane

#### Scenario: Fresh GitHub creation outranks an old actively updated repository

- **WHEN**一个 GitHub repository 在 window 内创建，另一个 old repository update 略新且 lifetime stars 很高
- **THEN**newly created repository 在 GitHub lane 排名第一
- **AND**lifetime stars 不改变顺序

Dedicated GitHub/Paper entry SHALL 使用与 News 相同的 corroboration confidence boundary：source-only
evidence 为 `low`；一个 independent non-watchlist realtime signal 为 `medium`；两个 independent
realtime source 或 WeChat watchlist signal + dedicated evidence 为 `high`。Why-now SHALL 展示 lane、
timestamp field、age band、signal-source count 与 watchlist reason。

#### Scenario: Dedicated-entry confidence reflects corroboration

- **WHEN**一个 dedicated item 无 realtime match，一个有 single non-watchlist match，另一个有 two-source 或 WeChat watchlist match
- **THEN**confidence 分别为 `low`、`medium`、`high`
- **AND**每个 why-now explanation 列出 actual lane 与 timestamp/corroboration reason

### Requirement: Cross-Source Dedupe and Corroboration

指向同一 normalized destination 或 exact normalized title 的 signal SHALL 合并为一个 Top item；
independent matching evidence SHALL 增加 corroboration context。URL normalization SHALL lowercase
scheme/host、移除 fragment 与 known tracking parameter、normalize trailing slash。Title normalization
SHALL 使用 Unicode NFKC、lowercase、remove punctuation、collapse whitespace；fuzzy semantic matching
不属于该 deterministic layer。

#### Scenario: One event appears on multiple sources

- **WHEN**两个 fresh signal 共享 normalized destination URL 或 equivalent title
- **THEN**daily briefing 只包含一个 Top entry
- **AND**保留全部 contributing source link 与 matched evidence
