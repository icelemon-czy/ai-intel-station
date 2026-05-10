# GitHub Delta Spec

## ADDED Requirements

### Requirement: GitHub Collection Module Preserves Current Behavior

The GitHub capability SHALL expose its collection behavior through the new collection layer while preserving the current CLI and output behavior.

#### Scenario: Collect one repository snapshot through the new structure

- **WHEN** the GitHub repo workflow is invoked through the reorganized code structure
- **THEN** it still writes the same repository Markdown and ResearchItem sidecar artifacts under `output/github/<owner-repo>/`

#### Scenario: Collect one search result set through the new structure

- **WHEN** the GitHub search workflow is invoked through the reorganized code structure
- **THEN** it still writes the same search Markdown and ResearchItem JSONL sidecar artifacts under `output/github/<query>/`
