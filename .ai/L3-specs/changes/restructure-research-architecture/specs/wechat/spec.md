# WeChat Delta Spec

## ADDED Requirements

### Requirement: WeChat Collection Module Preserves Current Behavior

The WeChat capability SHALL expose its collection behavior through the new collection layer while preserving the current CLI and output behavior.

#### Scenario: Collect one article through the new structure

- **WHEN** the WeChat workflow fetches one article through the reorganized code structure
- **THEN** it still writes the existing Markdown artifact, existing `images/` directory when applicable, and `research-item.json` sidecar under the article directory

#### Scenario: Preserve URL normalization through the new structure

- **WHEN** a pasted WeChat URL requires normalization before fetch
- **THEN** the reorganized code path still normalizes it before any network request is made
