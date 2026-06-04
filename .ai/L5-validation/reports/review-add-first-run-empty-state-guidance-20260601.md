# Review Report: add-first-run-empty-state-guidance

**Date**: 2026-06-01
**Reviewer**: review-tests skill
**Target**: `.ai/L3-specs/changes/add-first-run-empty-state-guidance/`
**Status**: ⚠️ Non-blocking gaps → APPROVED with Known Gaps

## Test Run

- ✅ All 5 empty-state tests pass
- ✅ No skip/only/pending markers
- ✅ No regressions

## Spec Coverage Table

| # | Req | Scenario | Test | Assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|------|-----------|------------|---------------|----------------|---------|
| 1 | First-Run ES | Dashboard | `test_dashboard_overview_exposes_empty_state_when_no_items` | 6 assertion (total_items=0 + 4 shape) | ✅ real `build_dashboard_overview` | ✅ all pass | ✅ would turn red | ✅ |
| 2 | First-Run ES | Library | `test_list_library_items_exposes_empty_state_when_no_results` | 6 assertion (items=[] + 4 shape) | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 3 | First-Run ES | Briefing | `test_preview_briefing_exposes_empty_state_when_no_items` | 6 assertion (item_count=0 + 4 shape) | ✅ real | ✅ all pass | ✅ would turn red | ✅ |
| 4 | First-Run ES | Collect first run | `test_app_jsx_renders_empty_state_panels_on_each_workspace` | 4× string-substring | ✅ real App.jsx | ⚠️ #5 weak-ish (text-match not real render) | ⚠️ substring survives if unrelated `empty_state` tokens exist | ⚠️ |
| 5 | First-Run ES | Purely informational | Indirectly covered by 6× `test_run_collect_*` + `test_list_library_items` + `test_preview_briefing_handles_empty_items_gracefully` | regression | ✅ | ✅ | ✅ | ✅ |

## Coverage Gaps (Non-blocking)

| Type | Description | Recommendation |
|------|-------------|----------------|
| Content assertion weak | `explanation` / `next_steps` only assert non-empty, not that they mention "Collect" or "backfill" | Add `"collect" in explanation.lower() or "collect" in " ".join(next_steps).lower()` |
| React real-render | Source-text match doesn't prove React renders the panel | Adopt React Testing Library + JSDOM |
| "Does not block form" | Scenario 4 AND clause "panel does not block the existing form" has no explicit assertion | Add tree-structure test that panel and form are siblings, not parent/child |

## Conclusion

- [ ] ✅ Pass
- [x] ⚠️ Non-blocking gaps
- [ ] ❌ Reject

**Decision**: APPROVED. Gaps registered in proposal.md Known Gaps. Status: `pending-review` → `approved`.
