# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。

## MODIFIED Requirements

### Requirement: Library Search & Inspection Layout

The Library page MUST arrange its primary controls and results so that the operator can (a) refine a search with minimal visual weight and (b) scan a wide result list with a side detail panel. The page MUST NOT use the legacy three-column layout where a tall description column crowds the result list.

#### Scenario: top filter bar holds all search controls

- **WHEN** the operator opens the Library page
- **THEN** the keyword input, source checkboxes, since/until date inputs, search action, and result count are all rendered in a single horizontal filter bar near the top of the page
- **AND** no element of the filter bar exceeds 320px wide on a 1280px viewport (the bar must wrap rather than overflow)

#### Scenario: results list occupies the dominant width

- **WHEN** the operator has searched Library
- **THEN** the result list panel is wider than the detail panel on a 1280px viewport
- **AND** at least 5 result cards are visible without scrolling on a 1024×768 viewport

#### Scenario: page-purpose / search-scope copy is demoted

- **WHEN** the operator opens the Library page
- **THEN** the page-purpose card and search-scope note are rendered as small eyebrow / collapsible copy
- **AND** the page-purpose card does NOT occupy its own full-width row above the filter bar

#### Scenario: detail panel groups metadata in a clear order

- **WHEN** the operator has a result selected
- **THEN** the detail panel shows: title, summary, source/type, authors, published/updated, tags, archive path, actions — in that order
- **AND** the title is the visually dominant element in the detail panel

#### Scenario: row card emphasizes scan fields

- **WHEN** the operator views the result list
- **THEN** each row card shows source, title, summary, and at least one of (published / tags / archive path)
- **AND** no row exceeds 4 lines of vertical text (compactness requirement)

#### Scenario: pagination stays in the result panel

- **WHEN** the operator scrolls the result list
- **THEN** pagination controls (`上一页` / `下一页` / page-size selector) live inside the result panel
- **AND** the detail panel does NOT contain any pagination control

#### Scenario: legacy three-column class names are not used

- **WHEN** the Library page is rendered
- **THEN** the legacy `library-layout` class is replaced (or removed) so the three-column grid no longer renders
- **AND** at least one new class identifies the two-column layout
