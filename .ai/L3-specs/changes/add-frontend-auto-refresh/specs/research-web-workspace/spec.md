# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Auto-Refresh

The Web workspace MUST poll the read-path data endpoints of the active section at a fixed interval while the topbar `Auto-refresh` toggle is on, and MUST stop polling when the toggle is off. Polling MUST NOT clear the user's in-progress inputs (keyword, sources, page, form fields, activeSource) and MUST NOT modify the API contract.

#### Scenario: Topbar exposes Auto-refresh toggle

- **WHEN** the operator opens the Web workspace
- **THEN** the topbar displays an `Auto-refresh` switch with a visible on/off state
- **AND** the toggle defaults to on

#### Scenario: Active read-path section is polled on an interval

- **WHEN** the topbar toggle is on AND the active section is one of `library`, `briefing`, `dashboard`, or `collect`
- **THEN** the workspace re-fetches that section's data endpoint at a 5-second interval
- **AND** each fetch replaces the section's data in place

#### Scenario: Toggle off stops polling

- **WHEN** the operator turns the topbar toggle off
- **THEN** polling stops within one interval
- **AND** no further fetch requests are issued for any section until the toggle is turned back on

#### Scenario: Polling preserves user inputs

- **WHEN** a polling fetch returns
- **THEN** the user's in-progress inputs (Library keyword / sources / page; Briefing form; Collect activeSource) are preserved across refreshes
- **AND** only the section's data is replaced, not its form state

#### Scenario: Section switch triggers an immediate refetch

- **WHEN** the operator switches the active section
- **THEN** the new section's data endpoint is fetched once immediately
- **AND** the new section joins the polling rotation while the toggle is on

#### Scenario: No backend contract change

- **WHEN** polling is enabled
- **THEN** the request shape, response shape, and HTTP method of the polled endpoints are unchanged
- **AND** no new query parameters are added
