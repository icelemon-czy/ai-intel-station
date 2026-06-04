# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Library Local-Search Scope Explanation

The Library page MUST display in-page copy that clarifies its search scope: searches act only on the local `output/` archive and the ResearchItem sidecar, and never trigger remote fetches against GitHub, arXiv, or WeChat. The copy MUST appear next to the search controls and the results panel.

#### Scenario: Search-area scope note

- **WHEN** the operator views the Library search panel
- **THEN** a short note is rendered explaining that searches only act on the local archive / sidecar and do not trigger remote fetches

#### Scenario: Filter-scope hint

- **WHEN** the operator views Sources, Keyword, or Since / Until controls
- **THEN** a short hint clarifies these filters only act on already-saved ResearchItems

#### Scenario: Results-area local-archive semantics

- **WHEN** the operator views the results list
- **THEN** a short note (or existing eyebrow / result meta) reinforces that each result comes from `output/` and points to the saved Markdown

#### Scenario: Empty results suggest Collect

- **WHEN** the operator has zero results
- **THEN** the empty-state guidance (provided by `add-first-run-empty-state-guidance`) suggests adjusting local filters or visiting Collect Workspace

#### Scenario: Search semantics are unchanged

- **WHEN** any of the above explanations is rendered
- **THEN** the Library query parameters, pagination, sort order, and `library/query.py` behavior are unchanged
- **AND** no remote search capability is introduced
