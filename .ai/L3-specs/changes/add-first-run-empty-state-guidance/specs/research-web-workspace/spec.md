# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: First-Run and Empty-State Guidance

Each primary Web workspace page (Dashboard, Library, Briefing, Collect) MUST display an in-page, explanatory empty-state panel when the local archive is empty, the search returns no items, no briefing preview is available, or no collect run has been started yet. The guidance MUST explain why the page is empty and point to the next action (collect, backfill, adjust filters, etc.).

#### Scenario: Dashboard shows empty-state when archive is empty

- **WHEN** the local archive contains no ResearchItems
- **THEN** Dashboard renders an in-page panel explaining the local archive is empty
- **AND** the panel points to Collect Workspace and the backfill command as next steps

#### Scenario: Library shows empty-state when no items match

- **WHEN** the operator runs a Library search that returns zero items
- **THEN** Library renders an in-page panel explaining the local search returned nothing
- **AND** the panel suggests adjusting keyword / sources / date range or visiting Collect Workspace

#### Scenario: Briefing shows empty-state when no preview is available

- **WHEN** the operator opens Briefing Workspace and no preview content has been generated
- **THEN** Briefing renders an in-page panel explaining the briefing depends on the local library
- **AND** the panel suggests running a collect / backfill or adjusting filters before previewing

#### Scenario: Collect shows empty-state before first run

- **WHEN** the operator opens Collect Workspace and has not yet run a collect operation
- **THEN** Collect renders an in-page panel explaining how to pick a source, fill inputs, and run manually
- **AND** the panel does not block the existing form or Run now button

#### Scenario: Empty-state is purely informational

- **WHEN** any of the above empty-states is rendered
- **THEN** the panel is in-page copy only — no modal, no onboarding wizard, no remote call
- **AND** it does not change collect, query, or briefing generation logic
