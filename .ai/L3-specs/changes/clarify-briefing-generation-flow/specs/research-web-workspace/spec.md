# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Briefing Generation Flow Explanation

The Briefing Workspace MUST display an in-page explanation of (a) where briefing content comes from, (b) the difference between `digest` and `reading-list` modes, and (c) the difference between Preview and Save. The explanation MUST be visible at the top of the control panel and MUST NOT change the briefing generation logic or output format.

#### Scenario: Briefing input source is explained

- **WHEN** the operator opens the Briefing Workspace
- **THEN** the control panel displays a short note explaining that briefings are derived from the local Library / ResearchItem sidecar and do not trigger remote fetches

#### Scenario: Mode differences are explained

- **WHEN** the operator views the Mode selector
- **THEN** `digest` and `reading-list` each have a one-line purpose description rendered next to the selector
- **AND** the description clarifies that digest summarizes items and reading-list queues items to read

#### Scenario: Preview vs Save is explained

- **WHEN** the operator views the Preview / Save actions
- **THEN** each action has a one-line purpose: Preview shows the derived Markdown in-page only, Save writes the file to `output/briefing/`
- **AND** after a Save, the saved file path is displayed and identified as a derived reading artifact

#### Scenario: Empty preview shows explanatory copy

- **WHEN** a preview returns no items
- **THEN** the preview area shows an explanatory note (reusing the empty-state panel) so the operator understands the briefing is empty because of filters, not a broken pipeline

#### Scenario: Explanations are purely informational

- **WHEN** any of the above explanations is rendered
- **THEN** they are in-page copy only — no modal, no wizard, no change to digest/reading-list Markdown format or save path
