# Review Report: fix-backend-relative-output-root-resolution (post-fix re-review)

**Date**: 2026-06-04
**Reviewer**: review-tests skill
**Target**: `.compass/context/L3-specs/changes/fix-backend-relative-output-root-resolution/`
**Status**: ✅ Pass

## Test Run

- ✅ 95/95 tests pass in `tests/test_web_workspace.py` (1 skip, see below)
- ✅ 3 tests directly cover the 3 Scenarios of this change
- ✅ All skip/only markers carry a reason (no naked `.skip` / `.only`)
- ✅ No regressions in the broader test suite

### Markers

| Marker | Location | Reason | Verdict |
|--------|----------|--------|---------|
| `pytest.skip("no seeded output/ at project root — cannot exercise path resolution")` | test_web_workspace.py:1627 | Skip when dev environment has no seeded output tree — guards against spurious green | ✅ justified |
| `pytest.skip("detail-panel not found in App.jsx — structure changed")` | test_web_workspace.py:2002 | Skip when App.jsx detail panel structure drifts — guards against brittle green | ✅ justified |
| `SKIPPED` summary line | test_web_workspace.py (L 92%) | The 1 skip is `test_library_detail_metadata_order` — unrelated to this change, no impact | ✅ not blocking |

## Spec Coverage Table

| # | Req | Scenario | Spec THEN (verbatim) | Test | File:Line | Actual assertion | Call-chain | Anti-patterns | Reverse-reason | Verdict |
|---|-----|----------|----------------------|------|-----------|------------------|------------|---------------|----------------|---------|
| 1 | serve_workspace Resolves Relative output_root | relative output_root resolved under wrong cwd still finds the data | "MUST resolve `output_root` to `<project_root>/output`; `/api/dashboard` MUST report the actual item count; count MUST be > 0" | `test_serve_workspace_resolves_relative_output_root_against_project_root` | test_web_workspace.py:1610 | `assert body.get("total_items", 0) > 0` (with diagnostic message identifying the wrong cwd) | ✅ real `serve_workspace(Path('output'))` + `subprocess.Popen` + wrong `cwd=web/` | ✅ all 7 pass | ✅ removing the `(project_root / output_root).resolve()` would yield body.total_items=0 and the assertion would fail red | ✅ |
| 2 | serve_workspace Resolves Relative output_root | absolute output_root is passed through | "MUST use that path verbatim (no project-root anchoring); the path printed to stdout reflects the absolute path" | `test_serve_workspace_passes_absolute_output_root_through_unchanged` | test_web_workspace.py:1674 | (a) `assert f"Using output root: {absolute_dir}" in text` (verbatim)  (b) `assert f"Using output root: {anchored}" not in text` (regression guard) | ✅ real `serve_workspace(Path('/abs'))` + subprocess with `-u` unbuffered + `communicate()` to drain stdout | ✅ all 7 pass | ✅ removing the `is_absolute()` branch would route the absolute path through `project_root / ...` and assertion (a) would fail red | ✅ |
| 3 | serve_workspace Resolves Relative output_root | relative path that does not exist under project root fails fast | "MUST still respond (return empty state) rather than crash; the printed 'Using output root' line MUST show `<project_root>/nonexistent-dir`" | `test_serve_workspace_with_nonexistent_relative_path_does_not_crash_dashboard` | test_web_workspace.py:1733 | (a) `assert body.get("total_items") == 0`  (b) `assert body.get("empty_state")`  (c) `assert f"Using output root: {expected}" in text` | ✅ real `serve_workspace(Path('nonexistent-fix-resolve-dir'))` + subprocess + urllib probe `GET /api/dashboard` while server alive + stdout capture | ✅ all 7 pass (try/except wraps urllib in diagnostic, not swallowing) | ✅ removing the resolve line would make the server print the original relative path AND the dashboard would still respond 200 — assertion (c) would fail red; removing the empty-state path in service.py would fail (b) | ✅ |

## Coverage Summary

| Capability | Requirement | Scenarios | ✅ Valid | 🔴 Defect | ❌ Missing |
|------------|-------------|-----------|----------|-----------|-----------|
| research-web-workspace (delta) | 1 | 3 | 3 (100%) | 0 (0%) | 0 (0%) |

## Anti-pattern Statistics

| Anti-pattern | Hits | Tests |
|--------------|------|-------|
| #1 assertion missing | 0 | — |
| #2 assertion too weak | 0 | — |
| #3 happy path only | 0 | — |
| #4 mock of unit under test | 0 | — |
| #5 assertion bypasses THEN | 0 | — |
| #6 tautological assertion | 0 | — |
| #7 swallowed exception | 0 | — |

## Coverage Gaps (Non-blocking)

| Type | Description | Recommendation |
|------|-------------|----------------|
| Boundary — `Path.resolve()` behaviour | The tests verify "what path gets printed" but not "what happens if that path is a symlink" or "what happens on Windows" | Out of scope: spec does not require symlink-aware resolution; Path.resolve is stdlib behaviour |
| `python -m workspace_web` invocation | Spec says "the server is started with `output_root = Path('output')`" — the tests cover the `serve_workspace(...)` function directly, not the CLI wrapper | Already covered in `test_research_item`-style integration tests for the CLI; not part of this delta |

## Fix Verification (vs. previous review)

| Previous Reject Reason | Status Now |
|------------------------|-----------|
| ❌ Scenario 2: absolute output_root is passed through — no test | ✅ **Covered** by `test_serve_workspace_passes_absolute_output_root_through_unchanged` (subprocess + stdout + verbatim assertion + re-anchored regression guard) |
| ❌ Scenario 3: relative path nonexistent fails fast — no test | ✅ **Covered** by `test_serve_workspace_with_nonexistent_relative_path_does_not_crash_dashboard` (subprocess + urllib probe + empty_state assertion + resolved-path assertion) |

Both previous gaps are now closed with real subprocess tests that actually call `serve_workspace` and observe the real stdout. No mocks, no patches, no shortcuts.

## Implementation Sanity Check

- `workspace_web/server.py:210-220` — `serve_workspace` resolves relative paths against `Path(__file__).resolve().parents[1]` (the project root) and passes absolute paths through unchanged. The fix is minimal (one line) and matches the spec exactly.
- `_create_handler(absolute_root)` is closed over the **resolved** path, so every API request uses the correct root regardless of cwd. ✅
- No regression risk: callers that already pass absolute paths see no change; callers that pass relative paths get the correct (and previously intended) behaviour.

## Conclusion

- [x] ✅ Pass
- [ ] ⚠️ Non-blocking
- [ ] ❌ Reject

**Decision**: PASS. Status: `pending-review` → `approved`. The change is ready for `/archive-change`.

---

## Reviewer Notes

- The subprocess + `-u` + `sys.stdout.flush()` + delayed `os._exit(0)` pattern in Scenarios 2 and 3 is correct and necessary: the server uses `os._exit(0)` for cleanup, which closes file descriptors before buffered stdout would otherwise flush. The 0.6s and 2.0s pre-exit sleeps are intentional to let the urllib probe and the `print()` line happen.
- The double assertion in Scenario 2 (verbatim + "not re-anchored") is a nice belt-and-braces: even if the verbatim check passes for the wrong reason (e.g. a partial path match), the regression guard catches it.
- Scenario 3's "wrong cwd on purpose" parameter (`cwd=str(project_root / "web")`) is a faithful reproduction of the original bug — exactly the launch path that produced the original 0-items dashboard.
