# Archive Output Delta Spec

## ADDED Requirements

### Requirement: Separate Raw Archives From Briefing Outputs

The workspace SHALL keep source-specific raw archives separate from derived briefing outputs for Obsidian consumption.

#### Scenario: Preserve source archives

- **WHEN** GitHub, papers, or WeChat collection runs
- **THEN** the raw source artifacts remain under the existing `output/github/`, `output/papers/`, and `output/wechat/` trees

#### Scenario: Write derived briefing artifacts

- **WHEN** the operator generates a digest, dossier, or reading list
- **THEN** the derived Markdown is written under a dedicated briefing output tree instead of being mixed into source-specific raw archive directories

### Requirement: Reuse Historical Archives For Derived Outputs

Derived briefing outputs SHALL be generatable from existing local archives without requiring a fresh re-fetch.

#### Scenario: Build a report from existing sidecars

- **WHEN** the operator generates a briefing from already archived source artifacts
- **THEN** the system can read local ResearchItem sidecars and produce the derived Markdown without contacting the remote source again
