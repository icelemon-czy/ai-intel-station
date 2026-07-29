# L3 Spec Construction

Use this reference to create or correct the system specification and capability specifications. Requirements are product truth, so confirmed user documents outrank code inference.

## Contents

- [Input authority](#input-authority)
- [Phase 1: read context](#phase-1-read-context)
- [Phase 2: system specification](#phase-2-system-specification)
- [Phase 3: capability map](#phase-3-capability-map)
- [Phase 4: capability requirements](#phase-4-capability-requirements)
- [Phase 5: confirmation and writing](#phase-5-confirmation-and-writing)
- [Quality checks](#quality-checks)

## Input authority

Apply this order:

1. Explicit user confirmation in the current task.
2. Current PRD, product specification, API contract, regulatory requirement, or approved change.
3. Existing confirmed L3 specifications.
4. Tests and implementation as evidence of current behavior.
5. Code inference as a draft only.

When sources conflict, show the conflict. Do not silently redefine the requirement to match the code.

Use these annotations when needed:

```markdown
<!-- ℹ️ Documented requirement; implementation not found or differs -->
<!-- ⚠️ Inferred from current code; requires confirmation -->
<!-- ⚠️ Sources conflict: [short explanation] -->
```

## Phase 1: read context

Read:

- `.compass/context/L1-codebase-map/overview.md`.
- Relevant feature READMEs and layer files.
- `.compass/context/L1-codebase-map/architecture.md` for cross-cutting runtime behavior.
- `.compass/context/L2-rules/global.md` for confirmed technical constraints.
- `.compass/context/L3-specs/specs/system.md`.
- `.compass/context/L3-specs/specs/_capability-template/spec.md`.
- User-provided requirement sources.

Inventory existing capability Specs and active changes so the initial build does not overwrite later decisions.

## Phase 2: system specification

Fill `specs/system.md` only with system-level facts:

- What the system is and is not responsible for.
- External actors and systems at the boundary.
- Cross-cutting authentication, authorization, audit, error, availability, performance, privacy, or compatibility requirements.
- Global constraints explicitly stated by an authoritative source.

Feature-specific behavior belongs in capability Specs. Implementation choices such as a particular cache or database belong in L1/L2 unless the choice itself is a confirmed requirement.

Each cross-cutting Requirement must include at least one Scenario with observable WHEN/THEN behavior.

## Phase 3: capability map

Start from requirement documents, then cross-check L1 features. Feature and capability are not always one-to-one:

| Situation | Action |
|:----------|:-------|
| Several features implement one business responsibility | Merge into one capability |
| One feature contains independent business responsibilities | Split into multiple capabilities |
| Pure infrastructure supports many capabilities | Keep as a system constraint or L1/L2 fact |
| A responsibility is a coherent subset of another | Use a child capability Spec |

Produce a proposed map before writing Specs:

| Capability | Related L1 features | Requirement source | Confidence | Open questions |
|:-----------|:--------------------|:-------------------|:-----------|:---------------|
| ... | ... | ... | confirmed / draft | ... |

Ask the user to confirm material boundary choices. Do not manufacture capability names only from directory names.

## Phase 4: capability requirements

For each confirmed capability:

1. Read its requirement source and related L1 feature documents.
2. Inspect implementation only to verify current behavior or locate differences.
3. Write a concise Purpose.
4. Write one independent `### Requirement:` per behavior or constraint.
5. Give every Requirement at least one `#### Scenario:` with concrete WHEN/THEN/AND outcomes.
6. Use SHALL/MUST for mandatory behavior, SHOULD for recommendations, and MAY for optional behavior.
7. Split child capabilities when one file grows beyond a coherent responsibility.

Do not put class names, file paths, library names, SQL schemas, or algorithm steps into requirements unless they are themselves contractual.

### Confidence handling

- Requirement source plus matching implementation: record normally.
- Requirement source without implementation: keep the requirement and annotate the implementation gap.
- Implementation without requirement source: draft and annotate as code-inferred.
- Conflicting requirement sources: stop that item and request a decision.

## Phase 5: confirmation and writing

Before treating code-inferred behavior as a confirmed Spec:

1. Show the capability map.
2. Show inferred Requirements and uncertainty annotations.
3. Ask focused business questions.
4. Incorporate confirmed answers.
5. Write files without deleting unrelated existing Requirements.

When updating an existing Spec, explain which Requirements were added, changed, preserved, or left unresolved.

## Quality checks

- Every Requirement has at least one `#### Scenario:`.
- Scenarios use WHEN/THEN/AND and observable results.
- Normative keywords match the intended strength.
- System-level and capability-level concerns are separated.
- Implementation details are excluded from product requirements.
- Documented-but-unimplemented and code-inferred behavior are visibly distinguished.
- No uncertain requirement is presented as confirmed without user approval.
