## ADDED Requirements

### Requirement: Business-First AI Navigation
The active `.ai` navigation and validation documents SHALL present the workspace using the business architecture and unified operator surface as the primary mental model.

#### Scenario: Read the active overview
- **WHEN** an operator or coding agent reads the active `.ai` overview and feature navigation
- **THEN** the documents present the unified operator surface and business layers before any source-specific historical structure

### Requirement: Clean Active AI Context
Active `.ai` specs, rules, and validation documents SHALL not contain leftover patch markers or ambiguous duplicate source-of-truth workflow copies.

#### Scenario: Read active spec and validation docs
- **WHEN** an operator or coding agent reads the active `.ai` specs, rules, and validation documents
- **THEN** those files are free of patch artifact markers and clearly identify the source-of-truth workflow path
