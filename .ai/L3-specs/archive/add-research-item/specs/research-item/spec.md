# Research Item Delta Spec

## ADDED Requirements

### Requirement: Unified ResearchItem Schema

The workspace SHALL define a shared `ResearchItem` abstraction for normalized cross-channel content.

#### Scenario: Normalize a GitHub repository snapshot

- **WHEN** repository metadata is fetched from GitHub
- **THEN** the system can represent it as a `ResearchItem` with source, item type, title, canonical URL, summary, timestamps, tags, and source-specific metadata

#### Scenario: Normalize a paper summary

- **WHEN** arXiv paper metadata is fetched
- **THEN** the system can represent it as a `ResearchItem` with title, authors, abstract summary, URLs, timestamps, and categories

#### Scenario: Normalize a WeChat article

- **WHEN** article metadata is extracted from a WeChat page
- **THEN** the system can represent it as a `ResearchItem` with title, source URL, publisher or author when available, publish time when available, and summary body metadata

### Requirement: Partial ResearchItems Are Allowed

The system SHALL allow `ResearchItem` instances with missing optional fields when a source cannot provide complete metadata.

#### Scenario: Missing optional metadata

- **WHEN** a source item has no author, no publish time, or no optional tag list
- **THEN** the system still emits a valid `ResearchItem` with empty or null optional fields instead of failing the whole item

### Requirement: Sidecar Persistence Within Source Directories

Normalized `ResearchItem` data SHALL be written as sidecar files inside the existing source-specific output directories, without changing the current Markdown artifact locations.

#### Scenario: Persist a repo-side sidecar

- **WHEN** a GitHub repository snapshot is generated
- **THEN** the output directory contains the existing Markdown file and a `research-item.json` sidecar in the same source directory

#### Scenario: Persist a search-side sidecar set

- **WHEN** a GitHub search result set is generated
- **THEN** the search output directory contains the existing `search.md` file and a `research-items.jsonl` sidecar for the normalized result items

#### Scenario: Persist a paper-side sidecar

- **WHEN** a paper Markdown file is generated
- **THEN** the same source directory contains a `<stem>.research-item.json` sidecar for that paper

#### Scenario: Persist a WeChat article sidecar

- **WHEN** a WeChat article Markdown file is generated
- **THEN** the same article directory contains a `research-item.json` sidecar

### Requirement: Historical Output Backfill

The workspace SHALL provide a backfill path that generates `ResearchItem` sidecars for existing source artifacts already stored under `output/`.

#### Scenario: Backfill historical outputs

- **WHEN** an operator runs the backfill command over existing `output/github`, `output/papers`, and `output/wechat` artifacts
- **THEN** normalized sidecar files are written for all parseable historical items while preserving the existing Markdown files
