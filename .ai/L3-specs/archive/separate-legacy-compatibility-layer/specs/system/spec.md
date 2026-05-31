## MODIFIED Requirements

### Requirement: Runnable Documented Entrypoints
Each supported capability SHALL have one documented workspace-level runtime path, and the workspace SHALL not require source-specific wrapper entrypoints after migration.

#### Scenario: Follow the migrated runtime path
- **WHEN** an operator follows the documented runtime command after migration
- **THEN** the command reaches the real behavior through the unified workspace surface and not through a legacy wrapper file
