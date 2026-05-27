# collect — Delta Spec

> 本文件描述对 `specs/collect/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: GitHub Collect API

[完整描述]

#### Scenario: Collect GitHub repo via CLI

- **WHEN** operator runs `research collect github owner/repo`
- **THEN** the system fetches the repository metadata and writes to output/github/<owner>-<repo>/

#### Scenario: Collect GitHub search via CLI

- **WHEN** operator runs `research collect github "query" --search`
- **THEN** the system performs GitHub search and writes matching repositories to output/github/search-<hash>/

### Requirement: Papers Collect API

[完整描述]

#### Scenario: Collect papers by category via CLI

- **WHEN** operator runs `research collect papers cs.AI --max 10`
- **THEN** the system fetches recent papers from arXiv category cs.AI and writes to output/papers/arXiv-<category>/

### Requirement: Web Collect Integration

[新增]

#### Scenario: Web collects GitHub via unified surface

- **WHEN** user submits GitHub collect form from Web Collect Workspace
- **THEN** the request routes through the unified collect surface with proper source-specific parameters

#### Scenario: Web collects papers via unified surface

- **WHEN** user submits papers collect form from Web Collect Workspace
- **THEN** the request routes through the unified collect surface with proper source-specific parameters