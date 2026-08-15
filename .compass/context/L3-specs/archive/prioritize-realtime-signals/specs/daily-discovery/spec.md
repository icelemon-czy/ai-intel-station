# Daily Discovery — Archived Delta Spec

## MODIFIED Requirements

### Requirement: Selective and Fault-Isolated Sweep

operator SHALL be able to select one or more configured GitHub, Papers, WeChat, Hacker News or X
sources; each source result MUST independently report succeeded, skipped and failed work, and a
single source failure MUST NOT prevent other source or briefing stages from completing.

#### Scenario: Run selected realtime sources

- **WHEN** operator selects Hacker News and WeChat
- **THEN**only those selected source collectors run
- **AND**each source's succeeded, skipped, failed and coverage notes are recorded separately

### Requirement: Agent-Operated Daily Intelligence

project-local daily intelligence Skill SHALL translate natural-language intent into existing
`research` actions, execute them, read the local signal artifact and return no more than 5 verified
fresh items plus source coverage. Normal flow MUST NOT require the user to edit YAML, read logs,
start Web or orchestrate CLI commands.

#### Scenario: Ask what is worth reading today

- **WHEN** user asks what is worth reading today without explicitly requesting a rerun
- **THEN**Agent first performs read-only inspection of today's run and briefing status
- **AND**a today's `ready`, `partial`, `no_fresh_signals` or `coverage_incomplete` non-dry-run signal artifact is reported without an immediate automatic retry
- **AND**a dry-run, failed, stale or legacy empty artifact does not masquerade as today's signal result

#### Scenario: Return a partial-success briefing

- **WHEN**today's run has successful signal sources and one or more failed sources
- **THEN**Agent returns the successful ranked items
- **AND**separately reports succeeded, skipped and failed source coverage

#### Scenario: Today's result has incomplete coverage and no Top items

- **WHEN**today's real artifact status is `coverage_incomplete`
- **THEN**Agent says there is no verifiable new result because coverage is incomplete rather than saying it was a quiet day
- **AND**Agent reports failed sources and waits for explicit rerun intent or a later schedule instead of immediately repeating the same network attempt
