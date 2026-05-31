# collect — Delta Spec

> 本文件描述对 `specs/collect/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: GitHub Collect API

The workspace SHALL expose a GitHub collect capability that performs preflight checks for gh CLI availability and authentication before executing collection.

#### Scenario: Collect GitHub repo via CLI

- **WHEN** operator runs `research collect github owner/repo`
- **THEN** the system checks gh CLI availability and authentication before collecting
- **AND** the system fetches the repository metadata and writes to output/github/<owner>-<repo>/

#### Scenario: Collect GitHub search via CLI

- **WHEN** operator runs `research collect github "query" --search`
- **THEN** the system checks gh CLI availability and authentication before collecting
- **AND** the system performs GitHub search and writes matching repositories to output/github/search-<hash>/

### Requirement: Papers Collect API

The workspace SHALL expose a papers collect capability that validates category validity before executing collection.

#### Scenario: Collect papers by category via CLI

- **WHEN** operator runs `research collect papers cs.AI --max 10`
- **THEN** the system validates the category is a valid arXiv category before collecting
- **AND** the system fetches recent papers from arXiv category cs.AI and writes to output/papers/arXiv-<category>/

### Requirement: Web Collect Preflight

[新增]

#### Scenario: Web GitHub collect with preflight

- **WHEN** user submits GitHub collect from Web
- **THEN** system performs preflight checks for gh CLI availability
- **THEN** if checks fail, display specific error and do not submit

#### Scenario: Web papers collect with preflight

- **WHEN** user submits papers collect from Web
- **THEN** system performs preflight checks for category validity
- **THEN** if checks fail, display specific error and do not submit