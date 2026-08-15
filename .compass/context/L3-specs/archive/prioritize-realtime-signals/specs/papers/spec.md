# Papers — Archived Delta Spec

## ADDED Requirements

### Requirement: Papers Evidence Role

Papers collected after this change MUST carry `signal_role=evidence`; legacy Papers with no role
SHALL also be interpreted as evidence by daily signal selection.

#### Scenario: A newly published paper has no social signal

- **WHEN**a Paper is published inside the freshness window but has no matching realtime signal
- **THEN**it does not independently seed the daily Top list
- **AND**it remains available as supporting evidence for a matching signal
