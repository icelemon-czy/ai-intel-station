# Signal Discovery — Delta Spec

## REMOVED Requirements

### Requirement: GitHub Destination Cap in News

**Reason**: destination-host 分类与 collect `source` 分层冲突；HN repo 发布应留在 Hacker News。
**Migration**: 删除 `github_news_max_items` 行为。existing YAML 中的该 field 忽略。HN
GitHub-target story 按 Hacker News quota 选择。

## MODIFIED Requirements

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
