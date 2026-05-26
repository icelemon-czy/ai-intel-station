# research-web-workspace Delta Spec

## ADDED Requirements

### Requirement: Dashboard Reflects Local Research Workspace

The first-phase React Web workspace SHALL provide a dashboard derived from the local archive and derived briefing outputs.

#### Scenario: Open dashboard with existing local archive

- **WHEN** the operator opens the local web workspace with existing sidecars and briefing artifacts under `output/`
- **THEN** the dashboard shows per-source archive counts and recent briefing artifacts derived from the local workspace
- **AND** it does not require any remote fetch to render the initial overview

#### Scenario: Dashboard surfaces archive gaps explicitly

- **WHEN** the local archive has missing sidecars, missing requested sources, or incomplete source coverage for the current overview
- **THEN** the dashboard marks those gaps explicitly instead of silently presenting the workspace as complete

### Requirement: Library Browses Local Research Items

The first-phase React Web workspace SHALL provide a Library view backed by local `ResearchItem` sidecars.

#### Scenario: Filter library results from local sidecars

- **WHEN** the operator enters a keyword and optional source or time filters in the Library view
- **THEN** the workspace shows matching local research items without triggering remote collection

#### Scenario: Inspect one local research item in detail

- **WHEN** the operator opens a research item from the Library results
- **THEN** the workspace shows the item title, summary, source, authors or publisher, tags, canonical URL, and archive path from local metadata

### Requirement: Briefing Workspace Previews And Saves Derived Reports

The first-phase React Web workspace SHALL let the operator configure a briefing request, preview the derived Markdown, and save the result under `output/briefing/`.

#### Scenario: Preview a local digest or reading list before save

- **WHEN** the operator chooses `digest` or `reading-list` and sets query filters in the Briefing Workspace
- **THEN** the workspace renders a preview derived from local sidecars before any file is written

#### Scenario: Save a briefing with partial source coverage

- **WHEN** the selected briefing input matches only some requested sources
- **THEN** the workspace still saves the derived Markdown under `output/briefing/`
- **AND** both the preview and saved result mark missing sources explicitly

### Requirement: MVP Navigation Stays Within Phase-One Scope

The first-phase React Web workspace SHALL limit the primary operator surface to Dashboard, Library, and Briefing Workspace.

#### Scenario: Open the phase-one web navigation

- **WHEN** the operator opens the first-phase local web workspace
- **THEN** the primary navigation exposes Dashboard, Library, and Briefing Workspace
- **AND** it does not expose collect or backfill execution controls in the MVP surface
