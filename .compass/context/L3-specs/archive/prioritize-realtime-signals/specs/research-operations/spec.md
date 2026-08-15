# Research Operations — Archived Delta Spec

## ADDED Requirements

### Requirement: Discovery-Only Social Source Selection

Hacker News and X SHALL be selectable through `research discover --source hackernews|x` and configured
daily discovery, but SHALL NOT add standalone `research collect hackernews|x` commands in this change.

#### Scenario: Select realtime sources for a discovery sweep

- **WHEN**operator runs `research discover --source hackernews,x`
- **THEN**the runtime dispatches only the configured Hacker News and X collectors
- **AND**CLI help and invalid-source guidance list both names without changing existing collect subcommands
