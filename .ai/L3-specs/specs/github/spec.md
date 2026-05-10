# GitHub Capability Specification

### Requirement: Save Repository Snapshots as Markdown
The GitHub research tool SHALL save repository snapshots as Markdown documents under `output/github/`.

#### Scenario: Fetch one repository
- **WHEN** the operator runs the repo mode command with `owner/repo`
- **THEN** the tool writes `output/github/<owner-repo>/README.md`

### Requirement: Save Search Results as Markdown
The tool SHALL support GitHub repository search and save results as Markdown.

#### Scenario: Search by query
- **WHEN** the operator runs the command with `--search`
- **THEN** the tool writes `output/github/<query>/search.md`

### Requirement: Include Open Issues in Repository Snapshots
Repository snapshots SHALL include open issue information when the current implementation fetches it.

#### Scenario: Repository has open issues
- **WHEN** repo mode fetches repository data
- **THEN** the generated Markdown includes the listed open issues returned by the current `gh` query

### Requirement: Surface GitHub CLI Failures
The tool SHALL fail explicitly when `gh` cannot satisfy the request.

#### Scenario: `gh` returns non-zero
- **WHEN** any `gh` subprocess call fails
- **THEN** the command surfaces a runtime error with the CLI stderr content