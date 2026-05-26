# system Delta Spec

## MODIFIED Requirements

### Requirement: Runnable Documented Entrypoints

Each supported capability SHALL have at least one documented local entrypoint that reaches the real runtime surface, whether through the CLI or the local Web workspace.

#### Scenario: Follow workspace docs for CLI capabilities

- **WHEN** an operator follows the documented CLI command in `.ai` or workspace README files
- **THEN** the command reaches the real CLI entrypoint instead of a placeholder or legacy wrapper path

#### Scenario: Follow workspace docs for the local Web workspace

- **WHEN** an operator follows the documented startup path for the local Web workspace
- **THEN** the workspace opens the real local Web surface that reads and writes through the same workspace archive rules

## ADDED Requirements

### Requirement: Shared Local Archive Truth Across Surfaces

The CLI surface and the local Web workspace SHALL share the same local archive and sidecar boundaries.

#### Scenario: Browse local archive content from the Web workspace

- **WHEN** the operator uses Dashboard or Library in the local Web workspace
- **THEN** the workspace reads local sidecars and derived outputs without performing remote collection

#### Scenario: Save a briefing from the Web workspace

- **WHEN** the operator saves a briefing from the local Web workspace
- **THEN** the derived artifact is written only under `output/briefing/`
- **AND** source-specific raw archives under `output/github/`, `output/papers/`, and `output/wechat/` remain unchanged
