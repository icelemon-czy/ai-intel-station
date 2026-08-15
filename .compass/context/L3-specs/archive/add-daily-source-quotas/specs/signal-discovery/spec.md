# Signal Discovery — Delta Spec

## MODIFIED Requirements

### Requirement: Explicit Signal and Evidence Roles

Every candidate SHALL retain its source role. WeChat/Hacker News/X remain realtime `signal` and may
enter only the `news` lane. GitHub repository/search and Papers remain `evidence`: they MUST NOT fill
the news quota, but MAY become primary reading entries in their own dedicated `github` or `papers`
lane. Exact normalized URL/title equivalence SHALL render once across lanes, using deterministic
ownership precedence `papers > github > news`. The owning dedicated entry retains matching realtime
signals as corroboration; lower-precedence lanes select their next eligible distinct candidate or
report a shortfall.

#### Scenario: Evidence enters only its dedicated lane

- **WHEN**fresh GitHub and Paper evidence exists without any realtime news signal
- **THEN**each may occupy only its matching dedicated lane
- **AND**neither item is counted toward the 5-item news quota

#### Scenario: Exact cross-lane duplicate has one owner

- **WHEN**an HN/X/WeChat signal has the same normalized URL or exact normalized title as a selected GitHub/Paper item
- **THEN**the artifact renders one dedicated-lane entry rather than a second News entry
- **AND**the realtime contribution raises corroboration while the News lane uses another eligible candidate or reports a shortfall

#### Scenario: Paper and GitHub candidates are exact duplicates

- **WHEN**a selected Paper and GitHub candidate share normalized URL or exact normalized title
- **THEN**the Paper lane owns the rendered entry and the GitHub lane selects its next distinct eligible candidate
- **AND**if no replacement exists, GitHub reports a shortfall and status cannot be `ready`

#### Scenario: WeChat minimum is reserved inside the news lane

- **WHEN**at least 2 verified fresh WeChat items and enough other ranked news signals exist
- **THEN**the news lane includes at least 2 WeChat items before filling its remaining positions
- **AND**the remaining news positions use the normal deterministic ranking across HN, X and unused WeChat items

#### Scenario: WeChat minimum cannot be met

- **WHEN**fewer than 2 verified fresh WeChat items exist but other news signals are available
- **THEN**other signals MAY fill the 5 total news positions
- **AND**quota coverage still reports the missing WeChat minimum and the briefing remains `partial`

`actual_wechat` SHALL count deduplicated rendered News entries containing at least one WeChat
contribution. Multiple raw WeChat candidates merged into one News entry count once; a mixed
WeChat/HN group also counts once. A WeChat signal attached only as corroboration to a dedicated
GitHub/Paper entry does not count toward the News WeChat minimum.

#### Scenario: Duplicate WeChat signals count after News dedupe

- **WHEN**two raw WeChat candidates normalize to one News entry and a separate WeChat/HN group normalizes to another
- **THEN**the two rendered News entries count as `actual_wechat=2`
- **AND**raw candidate count cannot falsely satisfy the WeChat minimum

### Requirement: Verifiable Freshness

News and Paper entries MUST use parseable `published_at` inside the configured freshness window.
GitHub entries MUST use parseable `updated_at`, falling back to `published_at` when update time is
absent. `discovered_at` and filesystem modification time MUST NOT substitute for source time. The
existing inclusive lower boundary, timezone normalization and future-skew exclusion apply to all lanes.

#### Scenario: Each lane applies its source timestamp

- **WHEN**a fresh Paper has `published_at`, a GitHub repository has recent `updated_at`, and another evidence item has only `discovered_at`
- **THEN**the Paper and GitHub item are eligible for their dedicated lanes
- **AND**the discovery-only evidence item is excluded as unverifiable

### Requirement: Deterministic Signal Ranking

News ranking SHALL retain 24-hour band, watchlist, corroboration, source-local engagement,
publication time and stable tie-breaks. Papers SHALL rank by publication time then normalized URL/title.
GitHub SHALL first prefer repositories created inside the freshness window, then rank by source
activity time (`updated_at` fallback `published_at`) and stable URL/title. Lifetime stars MUST NOT
outrank a fresher repository.

#### Scenario: Fresh GitHub creation outranks an old actively updated repository

- **WHEN**one GitHub repository was created inside the window and another old repository has a slightly newer update plus many lifetime stars
- **THEN**the newly created repository ranks first in the GitHub lane
- **AND**lifetime stars do not change that order

Dedicated GitHub/Paper entries SHALL use the same corroboration confidence boundary as News:
source-only evidence is `low`; one independent non-watchlist realtime signal is `medium`; two
independent realtime sources or a WeChat watchlist signal plus the dedicated evidence are `high`.
Why-now SHALL expose lane, timestamp field, age band, signal-source count and watchlist reason.

#### Scenario: Dedicated-entry confidence reflects corroboration

- **WHEN**one dedicated item has no realtime match, one has a single non-watchlist match, and one has two independent matches or a WeChat watchlist match
- **THEN**their confidence is respectively `low`, `medium` and `high`
- **AND**each why-now explanation names the actual lane and timestamp/corroboration reasons
