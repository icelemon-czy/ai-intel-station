# GitHub — Archived Delta Spec

## MODIFIED Requirements

### Requirement: Repository Search Snapshot

GitHub collection SHALL support repository search as recency-oriented supporting evidence. Search
MUST request and preserve available creation/update timestamps and MUST NOT present lifetime stars
ordering as a daily trend signal.

#### Scenario: Search repositories for daily discovery

- **WHEN** operator or discovery runtime submits a repository search query
- **THEN**system requests results ordered by recent update and saves search Markdown plus sidecars
- **AND**each result preserves available creation/update time and `signal_role=evidence`

#### Scenario: Persist search output path

- **WHEN**repository search artifact and sidecars are written successfully
- **THEN**the collection function returns the real Markdown Path
- **AND**the discovery run report never serializes a missing output path as success

## ADDED Requirements

### Requirement: GitHub Evidence Role

GitHub repository snapshots and repository search results collected after this change MUST carry
`signal_role=evidence`; legacy GitHub items with no role SHALL also be interpreted as evidence by
daily signal selection.

#### Scenario: A recently updated repository has no social signal

- **WHEN**a GitHub repository is created or updated inside the freshness window but has no matching realtime signal
- **THEN**it does not independently seed the daily Top list
- **AND**it remains available to corroborate a matching signal
