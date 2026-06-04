# Review Report: fix-backend-relative-output-root-resolution

**Date**: 2026-06-03
**Reviewer**: review-tests skill
**Target**: `.ai/L3-specs/changes/fix-backend-relative-output-root-resolution/`
**Status**: ❌ Reject (Scenarios 2 and 3 missing tests)

## Test Run

- ✅ The 1 existing test passes
- ✅ No skip/only/pending markers (both `pytest.skip()` calls have reasons)
- ✅ No regressions in 87/87 test_web_workspace.py

## Spec Coverage Table

| # | Req | Scenario | Test | Assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|------|-----------|------------|---------------|----------------|---------|
| 1 | serve_workspace Resolves Relative output_root | relative output_root resolved under wrong cwd | `test_serve_workspace_resolves_relative_output_root_against_project_root` | `body.get("total_items", 0) > 0` | ✅ real `serve_workspace` + subprocess + wrong cwd | ✅ all pass | ✅ would turn red | ✅ |
| 2 | serve_workspace Resolves Relative output_root | absolute output_root is passed through | ❌ MISSING | — | — | — | — | ❌ |
| 3 | serve_workspace Resolves Relative output_root | relative path nonexistent fails fast | ❌ MISSING | — | — | — | — | ❌ |

## Coverage Gaps (Must Fix)

| Type | Description | Recommendation |
|------|-------------|----------------|
| ❌ Scenario 2 missing | Absolute path (`Path('/abs/path')`) MUST be passed through verbatim and printed to stdout. No test covers this path. | Add a test that spawns serve_workspace with an absolute `output_root` and asserts the stdout line shows that absolute path. |
| ❌ Scenario 3 missing | A relative path that doesn't exist under project_root MUST NOT crash `/api/dashboard`. No test covers this path either. | Add a test that spawns serve_workspace with `Path('nonexistent-dir')` and asserts `/api/dashboard` returns HTTP 200 (empty state) and stdout shows the resolved path. |

## Reject Reasons

1. ❌ [Scenario 2: absolute output_root is passed through] — no test → /fix-bug Step 3B 补测试
2. ❌ [Scenario 3: relative path nonexistent fails fast] — no test → /fix-bug Step 3B 补测试

## Conclusion

- [ ] ✅ Pass
- [ ] ⚠️ Non-blocking
- [x] ❌ Reject

**Decision**: REJECT. Status: `pending-review` → `review-failed`. Two Scenarios lack tests; per skill rules this is a hard reject.
