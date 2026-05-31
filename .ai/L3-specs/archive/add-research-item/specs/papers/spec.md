# Papers Delta Spec

## ADDED Requirements

### Requirement: Persist ResearchItem Sidecars For Paper Outputs

The papers tool SHALL write normalized `ResearchItem` sidecars while preserving the current Markdown outputs.

#### Scenario: Generate one paper Markdown file

- **WHEN** a paper summary is written under `output/papers/arXiv-<category>/`
- **THEN** the tool also writes a `<stem>.research-item.json` sidecar in the same directory
