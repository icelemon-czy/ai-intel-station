# WeChat Delta Spec

## ADDED Requirements

### Requirement: Persist ResearchItem Sidecars For Article Outputs

The WeChat ingestion tool SHALL write a normalized `ResearchItem` sidecar while preserving the current Markdown and image outputs.

#### Scenario: Generate one WeChat article output

- **WHEN** the operator fetches a WeChat article successfully
- **THEN** the article directory contains the existing Markdown artifact, the existing `images/` directory when applicable, and a `research-item.json` sidecar
