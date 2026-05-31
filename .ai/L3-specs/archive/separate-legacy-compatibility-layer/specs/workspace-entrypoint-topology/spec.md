## ADDED Requirements

### Requirement: No Parallel Legacy Entrypoint Surface
The workspace SHALL not keep a second operator-facing entrypoint surface once the unified operator surface is introduced.

#### Scenario: Inspect the runtime entrypoint topology
- **WHEN** an operator or contributor looks for the documented runtime entrypoint
- **THEN** the workspace exposes only the unified operator surface rather than a second set of source-specific runtime scripts

### Requirement: Complete Entrypoint Migration
The runtime behavior that previously lived behind legacy top-level entrypoint files SHALL be migrated into the unified operator surface and core business layers.

#### Scenario: Execute a migrated workflow
- **WHEN** the operator runs a collect, query, briefing, or backfill action from the unified operator surface
- **THEN** the command completes without depending on a legacy wrapper entrypoint file
