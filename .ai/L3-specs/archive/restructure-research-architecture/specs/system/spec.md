# System Delta Spec

## ADDED Requirements

### Requirement: Business-Aligned Local Research Layers

The workspace SHALL evolve from source-specific scripts into business-aligned layers for collection, library, briefing, and publishing.

#### Scenario: Place shared logic outside source collectors

- **WHEN** the workspace supports cross-source query, filtering, or briefing behavior
- **THEN** that shared behavior lives in common library or briefing layers instead of being duplicated inside GitHub, papers, and WeChat collectors

#### Scenario: Keep collection responsibilities narrow

- **WHEN** a source-specific module handles GitHub, papers, or WeChat ingestion
- **THEN** it remains responsible for source collection and source-field mapping rather than report assembly or cross-source querying

### Requirement: Compatible Entrypoints During Restructure

The workspace SHALL preserve the currently documented CLI entrypoints while the internal structure is reorganized.

#### Scenario: Run an existing GitHub command

- **WHEN** the operator runs the documented GitHub repo or search command
- **THEN** the command still succeeds through the new internal layer boundaries without requiring a new user-facing command

#### Scenario: Run an existing papers or WeChat command

- **WHEN** the operator runs the documented papers or WeChat command
- **THEN** the command still reaches the real behavior and preserves the existing source-specific outputs
