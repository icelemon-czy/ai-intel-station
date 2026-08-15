# Validation Report: make-wechat-optional

**Date**: 2026-08-15
**Change**: `.compass/context/L3-specs/changes/make-wechat-optional/`
**Status**: PASS

## Executed checks

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py` | 84 passed |
| `.venv/bin/python -m pytest -q tests/test_discovery_state_migration.py tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py` | 89 passed |
| `.venv/bin/python -m unittest tests.test_discovery_runner` | 15 tests passed |
| `.venv/bin/python -m pytest -q tests -m "not wechat" --ignore=tests/test_discovery_runner.py --ignore=tests/test_wechat_collect.py --ignore=tests/test_wechat_e2e_live.py --deselect=tests/test_web_workspace.py::test_npm_test_in_web_runs_node_test_suite` | 467 passed, 26 skipped, 2 deselected, 4 subtests passed |
| `.venv/bin/python -m pytest -q -m wechat tests/test_research_item.py tests/test_wechat_collect.py` | 16 passed, 7 deselected |
| `.venv/bin/python -m pytest -q tests/test_l3_requirements.py tests/test_l3_policy_meta.py` | 7 passed |
| `.venv/bin/python -m research discover --dry-run` | exit 0; 9 planned source actions; briefing status `dry_run`; composition `5 News (WeChat optional maximum=2, minimum=0) + 1 GitHub + 1 arXiv` |
| `.venv/bin/python -m pytest -q tests/test_realtime_signals.py -k 'explicit_zero_wechat_minimum or optional_wechat_maximum_does_not_require'` | red before fix: 1 failed, 1 passed; green after fix: 2 passed, 67 deselected |
| `.venv/bin/python -m pytest -q tests/test_discovery_state_migration.py tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py` (post-review fix) | 91 passed |
| core regression command above (post-review fix) | 469 passed, 26 skipped, 2 deselected, 4 subtests passed |

## Contract evidence checked

- Default config parses `wechat_min_items=0` and `wechat_max_items=2`.
- Selection caps WeChat after News dedupe and uses non-WeChat replacement candidates.
- Production `generate_briefing` path covers HN-complete/optional-WeChat-failed for both nonempty
  and empty output, only-WeChat failure for both nonempty and empty output, and a simultaneous X
  failure that remains outcome-relevant.
- Explicit legacy positive `wechat_min_items` without a maximum expands the maximum to the whole
  News lane; explicit zero without a maximum retains default maximum 2; legacy `max_items` remains
  cap mode.
- A positive optional maximum with zero minimum loads successfully when WeChat is disabled and
  absent from `briefing.sources`, provided another viable News source exists.
- Config example exactly matches `render_example_config()`.
- Personal ignored config dry-run displays the new 5/2-optional/1/1 composition.
- Codex automation `ai` was updated in place and read back with status `ACTIVE`, daily 09:00
  recurrence, unchanged target task `019fb02a-2fa4-75f0-a818-465aa6f4062a`, and the full grouped
  max-7 / optional-WeChat / honest-failure prompt.

## Limitations

- No live WeChat public-index request was used as verification; the change is quota/outcome behavior,
  and live anti-bot availability is intentionally outside deterministic test scope.
- The core run skipped 26 environment-gated tests and deselected the Node workspace suite; no Web
  source or UI code changed in this change.
- During the core run an environment-blocked GitHub request printed a connection failure inside an
  existing fault-isolation test; the suite completed successfully and the event did not alter the
  local output artifacts used for this change.

## Review feedback

- Initial verify was `BLOCKED`: explicit zero minimum incorrectly expanded to whole-lane maximum,
  and optional maximum without a WeChat source lacked a meaningful validation assertion.
- Both gaps were reproduced/covered in `tests/test_realtime_signals.py`; the parser now expands only
  a parsed positive legacy minimum.
- Re-review verdict: PASS. Main briefing/signal-discovery/daily-discovery Specs and L1/L2/L5
  traceability were synchronized before archive.
