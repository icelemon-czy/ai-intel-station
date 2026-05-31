# Research Query Delta Spec

## ADDED Requirements

### Requirement: Query Local Research Library

The workspace SHALL provide a local query path over archived `ResearchItem` data spanning GitHub, papers, and WeChat sources.

#### Scenario: Query across multiple sources

- **WHEN** the operator searches the local research library by keyword or tag
- **THEN** the system returns matching items across all supported sources instead of requiring one source at a time

#### Scenario: Filter by source

- **WHEN** the operator restricts a query to one or more sources
- **THEN** the system returns only matching items from those selected sources

### Requirement: Optional Time Filtering

Time filtering SHALL remain optional for local research queries.

#### Scenario: Query without time constraints

- **WHEN** the operator runs a query without a time filter
- **THEN** the system searches all available archived items that satisfy the other filters

#### Scenario: Query with a time constraint

- **WHEN** the operator provides a time filter such as recent days or an explicit date range
- **THEN** the system returns only matching archived items that fall within that time window
