# Review Report: add-collect-source-purpose-cards

**Date**: 2026-06-01
**Reviewer**: review-tests skill
**Target**: `.ai/L3-specs/changes/add-collect-source-purpose-cards/`
**Status**: ⚠️ Non-blocking gap → APPROVED with Known Gap

## Test Run

- ✅ All 4 new tests pass
- ✅ No skip / only / pending markers
- ✅ No regressions in pre-existing test_run_collect_* tests

## Spec Coverage Table

| # | Req | Scenario | Test | Assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|------|-----------|------------|---------------|----------------|---------|
| 1 | Purpose Cards | GitHub | `test_github_collect_form_exposes_purpose_card_fields` | 4 keys shape + `output/github` + `owner/repo or search` | ✅ real `get_collect_form` | ✅ all pass | ✅ would turn red | ✅ |
| 2 | Purpose Cards | arXiv | `test_papers_collect_form_exposes_purpose_card_fields` | 4 keys shape + `output/papers` + `category or arxiv` | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 3 | Purpose Cards | WeChat | `test_wechat_collect_form_exposes_purpose_card_fields` | 4 keys shape + `output/wechat` + `url` | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 4 | Purpose Cards | Updates on switch | ❌ MISSING | — | — | — | — | ⚠️ |
| 5 | Purpose Cards | Purely informational | `test_collect_section_renders_purpose_card_using_form_metadata` + `test_run_collect_*` (regression) | App.jsx reads `formDefinition.{key}` | ✅ real App.jsx + real run_collect | ⚠️ #2 weak-ish (string substring) but acceptable for source-text test | ✅ would turn red | ✅ |

## Coverage Summary

- Requirements: 1
- Scenarios: 5
- ✅ Effective: 4 (80%)
- ⚠️ Gap: 1 (20%)
- 🔴 Defects: 0
- ❌ Missing tests: 1 (Scenario 4)

## Anti-pattern Hits

None. (one edge-case ⚠️ on string-substring assertion for JSX source test, but acceptable trade-off — would need JSDOM/React Testing Library to assert real rendering).

## Coverage Gaps (Non-blocking)

| Type | Description | Recommendation |
|------|-------------|----------------|
| Missing Scenario test | Scenario 4 "Purpose card updates when source switches" has no explicit test. Relies on React's standard re-render behavior. Indirectly validated by the 3 per-source tests. | Future change: add a React Testing Library test that asserts old card unmounts and new card mounts on source change. |

## Conclusion

- [ ] ✅ Pass
- [x] ⚠️ Non-blocking gap
- [ ] ❌ Reject

**Decision**: APPROVED. Single non-blocking gap (Scenario 4 has no explicit assertion) is recorded in proposal.md Known Gaps. Status: `pending-review` → `approved`.

## Status Update

proposal.md status: `pending-review` → `approved`
