# GitHub — Delta Spec

## MODIFIED Requirements

### Requirement: GitHub Evidence Role

GitHub repository snapshots and search results SHALL retain `signal_role=evidence`; legacy GitHub
items with no role SHALL also be interpreted as evidence. GitHub evidence MUST NOT independently
seed or fill the News lane, but verified fresh GitHub evidence MAY occupy the configured dedicated
GitHub lane as a primary reading entry.

#### Scenario: A fresh repository has no social signal

- **WHEN**a GitHub repository has verifiable recent source activity but no matching realtime signal
- **THEN**it may occupy the dedicated GitHub quota with `low` confidence
- **AND**it does not consume a News slot or claim social corroboration
