# Briefing — Archived Delta Spec

## ADDED Requirements

### Requirement: Daily Signal Briefing

Daily discovery SHALL generate a signal-first briefing containing at most the configured maximum
(default 5) verified fresh Top items. Each entry MUST expose what it is, why it matters now,
publication source/time, contributing signal links, matched evidence and confidence.

`why now` SHALL list the concrete ranking reasons that apply: age band, watchlist match, independent
signal-source count, evidence count and source-local engagement percentile. Confidence SHALL be
deterministic: `high` requires at least two independent signal sources, or one watchlist signal plus
at least one independent evidence item; `medium` requires one watchlist signal or one non-watchlist
signal plus independent evidence; every other verified fresh single-source signal is `low`. Coverage
failure SHALL be displayed separately and MUST NOT silently change a per-item confidence label.

Signal briefing outcome SHALL use one of these statuses: `ready` (Top items and complete realtime
coverage), `partial` (Top items with at least one realtime source failure), `no_fresh_signals`
(no Top items and complete realtime coverage), or `coverage_incomplete` (no Top items and at least
one realtime source failure). A generation crash SHALL be recorded as `failed`; planning SHALL be
`dry_run`. Existing generic digest/reading-list outputs SHALL be identified as `legacy` and MUST NOT
be treated as signal-first daily artifacts. Status SHALL appear in the Markdown header and in the
serialized DiscoveryReport / log summary.

#### Scenario: Fresh social signals are available

- **WHEN**one or more verified signals fall inside the configured freshness window
- **THEN**the generated daily signal artifact contains no more than 5 ranked entries
- **AND**each entry includes the required explanation and provenance fields

#### Scenario: Corroboration changes confidence and why-now reasons

- **WHEN**one fresh item has only one non-watchlist signal and another has two independent signal sources or a watchlist signal plus independent evidence
- **THEN**the first item is labeled `low` while the corroborated item is labeled `high`
- **AND**each why-now explanation names the actual age, watchlist, signal-source, evidence and engagement reasons used for ranking

### Requirement: Honest Empty Signal Result

A completed run with no verified fresh signal and complete coverage across this run's selected,
enabled realtime sources SHALL create an explicit `no_fresh_signals` artifact. A selected source that
is disabled is outside the attempted coverage set; an enabled selected source that fails or cannot
establish whether fresh items exist makes coverage incomplete. Empty artifacts MUST NOT be filled
with stale or evidence-only items.

#### Scenario: No fresh signal is available

- **WHEN**all local candidates are stale, timestamp-unknown or evidence-only
- **THEN**the daily artifact states that no verified fresh signal was found
- **AND**its machine-readable briefing status is `no_fresh_signals`

#### Scenario: No signal and coverage is incomplete

- **WHEN**no verified fresh signal is available and at least one configured realtime source fails
- **THEN**the daily artifact status is `coverage_incomplete`, not `no_fresh_signals`
- **AND**the wording says that no verified result can be concluded because source coverage is incomplete

#### Scenario: Keep existing generic briefing modes compatible

- **WHEN**an existing config explicitly selects `digest` or `reading-list`
- **THEN**the existing local-library rendering behavior remains available with `legacy` status
- **AND**a newly initialized config defaults to signal mode with `freshness_hours=48`, constrained to a maximum of 72, and `max_items=5`

### Requirement: Source Coverage in Daily Briefing

Daily signal briefing SHALL show configured source coverage independently from content ranking so a
blocked WeChat or X source is not misreported as a quiet day.

#### Scenario: One realtime source fails

- **WHEN**one configured realtime source fails and another produces usable signals
- **THEN**the briefing preserves and ranks successful signals
- **AND**the failed source and reason appear in coverage notes
