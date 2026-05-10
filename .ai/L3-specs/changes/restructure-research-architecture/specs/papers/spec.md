# Papers Delta Spec

## ADDED Requirements

### Requirement: Papers Collection Module Preserves Current Behavior

The papers capability SHALL expose its collection behavior through the new collection layer while preserving the current CLI and output behavior.

#### Scenario: Collect one category through the new structure

- **WHEN** the papers workflow fetches one supported category through the reorganized code structure
- **THEN** it still writes numbered Markdown files and per-paper ResearchItem sidecars under `output/papers/arXiv-<category>/`

#### Scenario: Continue category-level partial failure through the new structure

- **WHEN** one requested category fails and another succeeds through the reorganized code structure
- **THEN** the successful category still produces output and the failure remains explicitly surfaced to the operator
