# GitHub Delta Spec

## ADDED Requirements

### Requirement: Persist ResearchItem Sidecars For GitHub Outputs

The GitHub research tool SHALL write normalized `ResearchItem` sidecars while preserving the current Markdown outputs.

#### Scenario: Generate one repository snapshot

- **WHEN** the operator runs the repo mode command with `owner/repo`
- **THEN** the tool writes the existing `README.md` and a `research-item.json` sidecar under `output/github/<owner-repo>/`

#### Scenario: Generate one search result set

- **WHEN** the operator runs the search mode command with `--search`
- **THEN** the tool writes the existing `search.md` and a `research-items.jsonl` sidecar under `output/github/<query>/`
