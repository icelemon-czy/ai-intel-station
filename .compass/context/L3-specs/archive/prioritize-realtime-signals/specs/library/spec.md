# Local Library — Archived Delta Spec

## MODIFIED Requirements

### Requirement: Unified ResearchItem

Library SHALL use one backward-compatible ResearchItem contract for archive items, realtime signals
and supporting evidence. In addition to source, item type, title, canonical URL and output path, the
contract SHALL allow `discovered_at`, `signal_role` and `discovery_method` so daily intelligence can
distinguish observation time from publication time and signals from evidence.

#### Scenario: Load items from different sources

- **WHEN** Library scans multiple legacy and current source trees
- **THEN**all valid sidecars are parsed into one item shape
- **AND**missing new optional fields do not break legacy sidecars

#### Scenario: Save a newly discovered signal

- **WHEN**a realtime collector first observes a source item
- **THEN**its sidecar records `discovered_at`, `signal_role=signal` and the discovery method
- **AND**its source publication time remains separately represented by `published_at`

#### Scenario: Observe the same canonical item again

- **WHEN**a collector sees an already archived canonical item in a later run
- **THEN**the existing first `discovered_at` value is preserved
- **AND**mutable source metadata MAY be refreshed without presenting the item as newly discovered

#### Scenario: Backfill historical archive

- **WHEN**backfill reconstructs a sidecar from historical Markdown
- **THEN**it does not invent a current `discovered_at`
- **AND**the historical item cannot masquerade as newly discovered content
