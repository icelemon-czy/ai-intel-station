# Review Report: fix-auto-refresh-expose-poll-errors

**Date**: 2026-06-03
**Reviewer**: review-tests skill
**Target**: `.compass/context/L3-specs/changes/fix-auto-refresh-expose-poll-errors/`
**Status**: ⚠️ Non-blocking gap → APPROVED with Known Gap

## Test Run

- ✅ 4 new Python tests pass
- ✅ 5 new Node tests pass
- ✅ No skip/only/pending markers
- ✅ No regressions in 75/75 test_web_workspace.py + 18/18 Node

## Spec Coverage Table

| # | Req | Scenario | Test | Assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|------|-----------|------------|---------------|----------------|---------|
| 1 | Auto-Refresh Exposes Polling Errors | fetcher rejection fires onError | `fetcher rejection fires onError(section, error) and exposes lastError` | 7 assertion: errors.length, instanceof Error, message match, getLastError, isPolling | ✅ real controller + fake timers | ✅ all pass | ✅ would turn red | ✅ |
| 2 | Auto-Refresh Exposes Polling Errors | getLastError returns the most recent error | 2 Node tests: `getLastError returns null` + `dismissError(section) clears` | `=== null`, `instanceof Error`, `isPolling()` | ✅ real + fake | ✅ all pass | ✅ | ✅ |
| 3 | Auto-Refresh Exposes Polling Errors | successful fetch clears lastError | `successful fetch after a failure clears lastError for that section` | `instanceof Error` initial, `=== null` after recovery | ✅ real + fake | ✅ all pass | ✅ | ✅ |
| 4 | Auto-Refresh Exposes Polling Errors | User dismisses the error banner | `dismissError(section) clears` (Node) + `test_app_jsx_renders_poll_error_banner_in_each_section` (Python) | dismiss → null, PollErrorBanner ≥ 5 references in App.jsx | ✅ real | ✅ all pass | ✅ | ✅ |
| 5 | Auto-Refresh Exposes Polling Errors | Polling error is non-blocking | `test_app_jsx_poll_error_banner_is_non_blocking` | `banner_idx < form_idx` in LibrarySection | ✅ real | ✅ all pass | ✅ | ✅ |
| 6 | Auto-Refresh Exposes Polling Errors | Error message is safe to display | ❌ MISSING | — | — | — | — | ⚠️ |
| 7 (副) | Per-section isolation | — | `onError is per-section: errors on section A do not leak to section B` | cross-section error isolation | ✅ real + fake | ✅ all pass | ✅ | ✅ |
| 8 (副) | Module contract | — | `test_auto_refresh_controller_exposes_onError_getLastError_dismissError` | API names present in source | ✅ real | ✅ all pass | ✅ | ✅ |
| 9 (副) | React hook contract | — | `test_use_auto_refresh_react_hook_returns_lastError_and_dismissError` | hook return shape | ✅ real | ✅ all pass | ✅ | ✅ |

## Coverage Gaps (Non-blocking)

| Type | Description | Recommendation |
|------|-------------|----------------|
| ❌ Scenario 6 missing | "Error message is safe to display" — no test asserts that PollErrorBanner renders ONLY `error.message` and excludes stack/paths/tokens | Add a test that constructs an Error with stack/URL properties and asserts the rendered HTML doesn't contain them |
| ⚠️ React real-render | SSR test (Bug #2) covers hook return shape but not full state transition | Could fold into Bug #2's SSR suite |

## Conclusion

- [ ] ✅ Pass
- [x] ⚠️ Non-blocking
- [ ] ❌ Reject

**Decision**: APPROVED. Gap registered in proposal.md Known Gaps. Status: `pending-review` → `approved`.
