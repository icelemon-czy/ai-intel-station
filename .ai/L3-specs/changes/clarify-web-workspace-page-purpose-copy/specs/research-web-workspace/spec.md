# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Web Workspace Page Purpose Copy

Each primary Web workspace page (Dashboard, Library, Briefing, Collect) MUST display a short, consistent page-purpose card near the top of the section. The card MUST describe: (a) what the page is for, (b) what data it reads, (c) what the user gets after using it. The card is purely informational and MUST NOT change the page's logic, API, or output paths.

#### Scenario: Dashboard purpose card

- **WHEN** the operator opens the Dashboard
- **THEN** a purpose card is shown explaining it surfaces local archive health: total items, source coverage, missing sources, recent briefings, orphan markdown

#### Scenario: Library purpose card

- **WHEN** the operator opens the Library
- **THEN** a purpose card is shown explaining it searches the local ResearchItem sidecar (no remote fetch) and lets the operator open the saved Markdown

#### Scenario: Briefing purpose card

- **WHEN** the operator opens the Briefing Workspace
- **THEN** a purpose card is shown explaining it derives digest or reading-list Markdown from the local archive and writes saved briefings to `output/briefing/`

#### Scenario: Collect purpose card

- **WHEN** the operator opens the Collect Workspace
- **THEN** a purpose card is shown explaining it pulls material from GitHub, arXiv, or WeChat into `output/<source>/`

#### Scenario: Purpose cards are consistent in style

- **WHEN** any of the four purpose cards is rendered
- **THEN** they share the same component / class so the user gets a consistent visual language across all four pages

#### Scenario: Purpose cards are purely informational

- **WHEN** any of the four purpose cards is rendered
- **THEN** they do not add modal dialogs, onboarding wizards, or new data models
- **AND** they do not change the API, output path, or generation logic
