# Review Report: clarify-briefing-generation-flow

**Date**: 2026-06-01
**Reviewer**: review-tests skill
**Target**: `.ai/L3-specs/changes/clarify-briefing-generation-flow/`
**Status**: ⚠️ Non-blocking gaps → APPROVED with Known Gaps

## Test Run

- ✅ All 4 new tests pass
- ✅ No skip/only/pending markers
- ✅ Reuses Change 2's `test_preview_briefing_exposes_empty_state_when_no_items` for empty-preview scenario
- ✅ No regressions

## Spec Coverage Table

| # | Req | Scenario | Test | Assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|------|-----------|------------|---------------|----------------|---------|
| 1 | Briefing Flow | Input source | `test_briefing_flow_notes_explains_input_source` | `local` + (`library` or `researchitem` or `sidecar`) | ✅ real `briefing_flow_notes()` | ✅ all pass | ✅ would turn red | ✅ |
| 2 | Briefing Flow | Mode diff | `test_briefing_mode_purposes_exposes_both_modes` | both keys + `summariz` in digest + `read` in reading-list | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 3 | Briefing Flow | Preview vs Save | `test_briefing_action_purposes_distinguishes_preview_and_save` | preview/save keys + keywords + `output/briefing` in save | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 4 | Briefing Flow | Empty preview | reused `test_preview_briefing_exposes_empty_state_when_no_items` | exists in Change 2 | ✅ | ✅ | ✅ | ✅ |
| 5 | Briefing Flow | Purely informational | `test_app_jsx_renders_briefing_flow_explanations` + regression tests | App.jsx metadata plumbing + test_save_briefing | ✅ real App.jsx | ⚠️ #2/#5 weak-ish substring | ✅ substring survives, but most assertions check specific keys | ✅ |

## Coverage Gaps (Non-blocking)

| Type | Description | Recommendation |
|------|-------------|----------------|
| "Saved artifact" not asserted in render | Scenario 3 AND "after Save, file path displayed and identified as derived artifact" — only backend metadata `saved_artifact` field tested, not React render of "derived reading artifact" text | Add assertion that BriefingSection JSX contains the artifact label |
| React real-render | Same project-level JSDOM gap | Adopt React Testing Library |

## Conclusion

- [ ] ✅ Pass
- [x] ⚠️ Non-blocking gaps
- [ ] ❌ Reject

**Decision**: APPROVED. Gaps registered in proposal.md Known Gaps. Status: `pending-review` → `approved`.
