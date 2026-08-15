# Daily Discovery — Delta Spec

## MODIFIED Requirements

### Requirement: Config Initialization and Validation

Newly initialized signals config SHALL be internally viable for its default quotas: it SHALL enable
and configure at least one news source, the WeChat watchlist needed by `wechat_min_items=2`, GitHub
targets and Paper categories. Signals config SHALL validate quota bounds/relations and positive-quota
source membership, enabled state and target availability before any network action. Explicit
digest/reading-list config SHALL keep legacy rendering and SHALL NOT require signal quota sources.

#### Scenario: Initialize a viable quota config

- **WHEN**operator runs `research init-config`
- **THEN**the generated YAML contains 5 News / 2 WeChat-minimum / 1 GitHub / 1 Paper quotas and viable enabled targets
- **AND**network-free dry-run validates the 7-item composition

#### Scenario: Positive quota has no viable source

- **WHEN**signals config requires a lane/source that is absent from `briefing.sources`, disabled or has no configured work
- **THEN**validation reports all discoverable source/quota problems before collection
- **AND**no network request starts

### Requirement: Agent-Operated Daily Intelligence

The daily intelligence Skill SHALL return the local quota-composed artifact grouped as arXiv,
GitHub and News, with at most the configured lane total (default 7), plus source coverage and quota
shortfalls. Normal flow MUST NOT present a missing required lane as a complete daily briefing.

#### Scenario: Ask what is worth reading today

- **WHEN**user asks what is worth reading today and a usable quota-composed artifact exists
- **THEN**Agent returns up to 1 arXiv item, 1 GitHub item and 5 News items under the default config
- **AND**the News group contains at least 2 WeChat items when fresh eligible WeChat content exists
- **AND**each returned item says what it is and why it matters now

#### Scenario: Return a partial quota briefing

- **WHEN**today's artifact contains eligible items but one or more lane quotas are unfilled
- **THEN**Agent returns the successful items grouped by lane
- **AND**separately reports missing lane counts and succeeded/skipped/failed source coverage
