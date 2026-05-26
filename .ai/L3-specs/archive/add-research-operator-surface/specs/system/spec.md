## MODIFIED Requirements

### Requirement: Runnable Documented Entrypoints
Each supported capability SHALL be reachable from the workspace through one documented operator-facing command surface.

#### Scenario: Follow workspace docs
- **WHEN** an operator follows the command documented in `.ai` or workspace README files
- **THEN** the command reaches the unified workspace operator surface instead of requiring a source-specific wrapper path
