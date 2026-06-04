# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更（针对 `add-frontend-auto-refresh` 的 known gap）。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Library Form State Survives Section Switches

The Library page's in-progress form state (keyword, sources, since, until, page, pageSize) MUST survive a section switch away from Library and back. Specifically: if the operator has typed a custom keyword in Library, switches to Dashboard or any other section, and then switches back to Library, the keyword MUST still be the user-typed value, not the default.

#### Scenario: user-typed keyword survives switch away and back

- **WHEN** the operator types a keyword in Library (e.g. "transformer")
- **AND** switches the active section away from Library (e.g. to Dashboard)
- **AND** switches the active section back to Library
- **THEN** the keyword input MUST still display "transformer"
- **AND** the search results MUST reflect the user's last-typed query

#### Scenario: user-selected sources survive switch away and back

- **WHEN** the operator toggles a source checkbox in Library (e.g. un-checks "wechat")
- **AND** switches the active section away
- **AND** switches back
- **THEN** the "wechat" checkbox MUST still be un-checked
- **AND** no default-revert of the source list happens

#### Scenario: page index survives switch away and back

- **WHEN** the operator advances to page 3 in Library results
- **AND** switches away and back
- **THEN** the result list MUST show page 3 (not page 1)

#### Scenario: state lives in App, not in section component

- **WHEN** the App component is inspected at the source level
- **THEN** the Library form state is owned by App (or a lifted state holder), not by the LibrarySection component
- **AND** LibrarySection receives the form + setter as props (or via a context that survives unmount)

#### Scenario: other sections' form state is unaffected

- **WHEN** the operator types a keyword in Library and switches to Briefing
- **THEN** Briefing's form state (mode / title) is initialized independently
- **AND** is NOT polluted by Library's previous state
