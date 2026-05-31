# research-operations — Delta Spec

> 本文件描述对 `specs/research-operations/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Unified Workspace Command Surface

The workspace SHALL expose one operator-facing command surface that organizes the research workflow by business action instead of by source-specific script.

#### Scenario: Collect from GitHub through the workspace surface

- **WHEN** the operator runs the unified workspace command for `collect github owner/repo`
- **THEN** the command reaches the GitHub collect implementation and writes artifacts under `output/github/`

#### Scenario: Collect from papers or WeChat through the workspace surface

- **WHEN** the operator runs the unified workspace command for `collect papers ...` or `collect wechat ...`
- **THEN** the command reaches the corresponding collect implementation without requiring a source-specific top-level script path

#### Scenario: Web collect interface integration

- **WHEN** the operator interacts with the Web Collect Workspace
- **THEN** the interactions route through the unified command surface with proper Web-specific input adaptation

### Requirement: Workspace Query And Briefing Actions

The workspace command surface SHALL expose local-first `query`, `briefing`, and `backfill` actions.

#### Scenario: Query local research items through the workspace surface

- **WHEN** the operator runs the unified workspace command for `query <keyword>`
- **THEN** the command loads local sidecars and prints a result view without performing any remote fetch

#### Scenario: Generate a briefing through the workspace surface

- **WHEN** the operator runs the unified workspace command for `briefing digest <keyword>` or `briefing reading-list <keyword>`
- **THEN** the command writes the derived Markdown under `output/briefing/`

### Requirement: Partial Progress Continues

When a workspace operation requests multiple logical sources or downstream steps, the command SHALL continue with successful parts and report the missing or failed parts explicitly.

#### Scenario: Briefing requests a missing source

- **WHEN** the operator requests a briefing that names a source not present in the local archive
- **THEN** the workspace command still writes the briefing and marks the missing source explicitly