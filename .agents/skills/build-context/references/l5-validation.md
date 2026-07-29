# L5 Evidence and Traceability

Use this reference to validate L3 structure, trace requirements to implementation and tests, design tests for gaps, and create evidence-based validation reports.

## Contents

- [Integrity rules](#integrity-rules)
- [Phase 1: choose scope](#phase-1-choose-scope)
- [Phase 2: structural validation](#phase-2-structural-validation)
- [Phase 3: forward traceability](#phase-3-forward-traceability)
- [Phase 4: reverse traceability](#phase-4-reverse-traceability)
- [Phase 5: test design](#phase-5-test-design)
- [Phase 6: reports](#phase-6-reports)
- [Quality checks](#quality-checks)

## Integrity rules

- `verified` means the implementation and relevant test evidence were actually inspected.
- A passing test command alone does not prove that a Scenario is covered.
- Test existence alone does not prove that its assertions discriminate correct from incorrect behavior.
- Do not change product requirements merely to make current code pass validation.
- Record missing evidence as `untested`, `partial`, `unimplemented`, or `no-spec`.
- Use commands discovered from project configuration; never guess test commands.

Read `.compass/context/L5-validation/validation-rules.md` before validating.

## Phase 1: choose scope

Select one of:

- A single capability domain.
- Domains affected by an active change.
- A full validation sweep.

Read:

- Relevant L3 Specs.
- Matching L1 feature and architecture documents.
- `.compass/context/L2-rules/testing.md`.
- Existing traceability, test-spec, and report files.
- Real implementation and test files.

If L2 testing rules are blank or commands conflict, resolve or report that before relying on execution results.

## Phase 2: structural validation

For `system.md` and each selected capability Spec, check:

- Every Requirement has at least one Scenario.
- Scenario headings use four `#` characters.
- WHEN/THEN/AND clauses are present and observable.
- SHALL/MUST/SHOULD/MAY are used consistently.
- Requirements describe behavior rather than implementation.
- System boundary and cross-cutting requirements are present when relevant.

Fix formatting only when meaning is unchanged. Ask the user before changing requirement semantics.

## Phase 3: forward traceability

For every selected Scenario:

1. Read its Requirement and normative strength.
2. Use L1 navigation to locate the implementation entrypoint.
3. Read the actual call path that handles the WHEN condition and produces the THEN result.
4. Locate tests that claim to cover the behavior.
5. Read setup, inputs, mocks, execution, assertions, and teardown.
6. Run the narrowest discovered test command when execution is in scope and safe.
7. Assign a status with file evidence.

| Status | Required evidence |
|:-------|:------------------|
| `verified` | Matching implementation plus a meaningful test that checks the Scenario outcome |
| `untested` | Implementation found, no meaningful test coverage |
| `partial` | Only part of WHEN/THEN behavior is implemented or tested |
| `unimplemented` | Requirement exists, implementation not found |

SHOULD Requirements may remain unimplemented, but the status must still be explicit. MAY Requirements can be recorded without treating absence as a defect.

## Phase 4: reverse traceability

From L1, identify core public APIs, business rules, transformations, and boundary validation. For each:

1. Read the source behavior.
2. Search selected Specs for an equivalent Requirement.
3. Mark important unmatched behavior as `no-spec`.

Ignore trivial utilities, generated code, and framework glue unless they implement contractual behavior.

For a full sweep, also check:

- Cross-cutting system Requirements across domains.
- Contradictory terms or behaviors between capability Specs.
- Domain dependencies not represented in Specs.

## Phase 5: test design

Read `.compass/context/L5-validation/test-specs/_domain-template.md`.

For every `untested`, `partial`, or `unimplemented` Scenario, design concrete cases as appropriate:

- Happy path.
- Edge cases such as empty, zero, maximum, special characters, and boundary quantities.
- Error paths such as invalid input, unavailable dependencies, missing permission, and timeout.
- Boundary or concurrency cases when the Requirement implies them.

Every case must contain specific inputs and expected outcomes, plus setup and teardown. Do not duplicate cases already covered by meaningful tests.

Test design is not validation evidence. Keep the Scenario non-verified until implementation and tests are actually checked.

## Phase 6: reports

Update `.compass/context/L5-validation/traceability/<domain>.md` using the current template. Include concrete implementation and test paths.

For a review or full sweep, write `.compass/context/L5-validation/reports/<date>-<scope>.md` with:

- Scope and evidence inspected.
- Requirement and Scenario counts.
- Status totals.
- Domain-level findings.
- Prioritized gaps.
- Commands run and their actual results.
- Uncertainty and work not performed.

Do not claim complete validation when only a subset was checked.

## Quality checks

- Every status links to inspected evidence or explicitly states that evidence is missing.
- `verified` rows include both implementation and meaningful test coverage.
- Reverse traceability covers core behavior without inventorying trivial code.
- Test specs contain concrete data and expected results.
- Reports distinguish inspected facts from recommendations.
- Failed or unavailable checks remain visible; they are not rewritten as success.
