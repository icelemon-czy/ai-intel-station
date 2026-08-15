# Briefing — Delta Spec

## MODIFIED Requirements

### Requirement: Daily Signal Briefing

Daily discovery SHALL generate a quota-composed briefing with three independently ranked lanes:
`news`, `github` and `papers`. Newly initialized/default config SHALL request 5 verified fresh news
items including at least 2 WeChat items, 1 fresh GitHub item and 1 fresh Paper item, for at most 7
entries total. Each entry MUST expose
what it is, why it matters now, publication/activity source and time, contributing links, matched
corroboration and confidence.

The news lane SHALL keep the existing deterministic confidence and why-now contract. A dedicated
GitHub/Paper entry with no independent realtime corroboration SHALL be `low`; a matching realtime
signal SHALL raise confidence using the same one-source/two-source rules. Coverage failure SHALL be
displayed separately and MUST NOT silently change confidence.

Signal outcome SHALL be `ready` only when all configured lane/minimum quotas are met and source
coverage is complete. With at least one entry, any quota shortfall, attempted-source failure or
unattempted positive-quota source SHALL produce `partial`. With zero entries, complete attempted
coverage SHALL produce `no_fresh_signals`; an attempted-source failure or unattempted positive-quota
source SHALL produce `coverage_incomplete`.
Generation crash SHALL remain `failed`, planning `dry_run`, and generic digest/reading-list `legacy`.

For signals mode, source/config state SHALL have these semantics:

| State | Validation / runtime result |
|---|---|
| Positive GitHub/Paper/WeChat quota but source absent from `briefing.sources`, disabled, or has no configured target | config error before network |
| `news_items>0` but no realtime source inside `briefing.sources` is enabled with configured work | config error before network |
| Explicit `--source` run with `news_items>0` attempts no viable News provider | unattempted News coverage; nonempty=`partial`, empty=`coverage_incomplete` even if local fresh News exists |
| Explicit `--source` omits GitHub/Paper/WeChat required by a positive quota | unattempted required coverage; never `ready` |
| Required source succeeds but yields too few fresh eligible items | quota shortfall, not source failure |
| Any attempted selected enabled source fails | incomplete coverage, including GitHub/Papers |
| Source has zero quota and is disabled or not selected | outside required coverage |

#### Scenario: Default daily composition is complete

- **WHEN**the freshness window contains at least 5 ranked news signals, 1 eligible GitHub item and 1 eligible Paper
- **THEN**the daily artifact contains 7 entries grouped as 5 News, 1 GitHub and 1 arXiv
- **AND**at least 2 of the 5 News entries come from WeChat
- **AND**its status is `ready` when attempted source coverage is complete

#### Scenario: A required lane cannot fill its quota

- **WHEN**at least one eligible item exists but the fresh GitHub, Paper or news candidates cannot fill the configured lane quota
- **THEN**the artifact preserves all eligible entries and reports expected, actual and missing counts per lane
- **AND**its status is `partial` without filling the gap from stale, timestamp-unknown or another lane

#### Scenario: Corroboration changes confidence and why-now reasons

- **WHEN**a dedicated GitHub/Paper entry or news item has matching independent realtime signals
- **THEN**confidence reflects the actual number/type of corroborating sources
- **AND**why-now names its lane, source timestamp field, age band and corroboration reasons

### Requirement: Honest Empty Signal Result

A completed run SHALL apply freshness independently to all configured lanes. Empty or short lanes
MUST NOT be filled with stale, timestamp-unknown or wrong-lane items. New signals config defaults
SHALL use `news_items=5`, `wechat_min_items=2`, `github_items=1`, `paper_items=1`.

New signals quota fields SHALL be integers with `news_items` in 1..10, `wechat_min_items` in 0..news_items,
and `github_items` / `paper_items` in 0..5; total entries MUST NOT exceed 20. Positive dedicated or
WeChat quotas trigger the source/target validation matrix above. A legacy `max_items` value in 1..10
is accepted only when none of the four new quota fields is present. It preserves legacy cap mode:
select at most `max_items` News entries, set dedicated/WeChat minimums to zero, and do not mark a
nonempty result partial merely because fewer than `max_items` exist. Quota fields in explicit
digest/reading-list mode are ignored for rendering and SHALL NOT change legacy behavior.

#### Scenario: Legacy max-items config stays backward compatible

- **WHEN**an existing signals config contains `max_items: 5` and no explicit lane quota fields
- **THEN**the runtime interprets it as a cap of 5 News items with zero WeChat/GitHub/Paper minimum
- **AND**one fresh News item with complete attempted coverage remains `ready`, while digest/reading-list behavior is unchanged

#### Scenario: Selective run omits every News provider

- **WHEN**new quota mode requires News but an explicit selective run attempts only GitHub/Papers while local fresh News sidecars exist
- **THEN**local News MAY remain visible but the result cannot be `ready`
- **AND**nonempty output is `partial`; zero output is `coverage_incomplete`

#### Scenario: Conflicting or invalid quota fields are rejected

- **WHEN**a signals config mixes `max_items` with any new quota field, violates bounds/relations, or configures a positive quota without a viable source
- **THEN**config validation reports all discoverable quota/source problems in actionable errors
- **AND**no discovery network action begins
