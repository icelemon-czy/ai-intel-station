# Papers — Delta Spec

## MODIFIED Requirements

### Requirement: Papers Evidence Role

Papers SHALL retain `signal_role=evidence`; legacy Papers with no role SHALL also be interpreted as
evidence. Paper evidence MUST NOT independently seed or fill the News lane, but a verified fresh
Paper MAY occupy the configured dedicated arXiv lane as a primary reading entry.

#### Scenario: A fresh Paper has no social signal

- **WHEN**a Paper has verifiable recent `published_at` but no matching realtime signal
- **THEN**it may occupy the dedicated arXiv quota with `low` confidence
- **AND**it does not consume a News slot or claim social corroboration
