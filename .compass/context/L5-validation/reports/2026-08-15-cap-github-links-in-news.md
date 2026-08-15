# Validation Report: cap-github-links-in-news

**Date**: 2026-08-15
**Change**: `.compass/context/L3-specs/archive/cap-github-links-in-news/`
**Status**: PASS

## Executed checks

| Command | Result |
|---|---|
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_discovery_config.py` | red before implementation: 15 failed, 77 passed; green after implementation: 92 passed |
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py tests/test_restructure_research_architecture.py tests/test_briefing_marker.py` | 116 passed, 4 subtests passed |
| same adjacent/core command after verify fixes | 117 passed, 4 subtests passed |
| adjacent/core command plus L3 structure/policy checks after Spec merge/archive | 124 passed, 4 subtests passed |
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen research discover --dry-run` | exit 0; configured GitHub destination maximum 1; actual/excluded unavailable |
| local `generate_briefing(load_config(DEFAULT_CONFIG_PATH))` production call | wrote `output/briefing/signals/daily-2026-08-15-7.md`; 7 items; News GitHub destinations 1/1; 3 cap exclusions; status partial only because no source reports were supplied |
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen --extra dev python -m pytest -q` | 514 passed, 27 skipped, 15 collection errors and 3 failures unrelated to this diff |

## Contract evidence checked

- Quota config defaults `github_news_max_items=1`, validates integer range and relation to
  `news_items`, rejects mixed legacy config, remains absent in pure legacy signals mode, and is
  ignored by digest/reading-list.
- A non-default YAML maximum of zero is loaded through the production config and runner path; two
  GitHub candidates are excluded, the external replacement is rendered, and the artifact reports
  actual/maximum/excluded as `0/0/2`.
- Post-cross-lane-dedupe greedy selection caps exact `github.com` and subdomain destinations,
  rejects `github.io`/lookalikes, uses later non-GitHub replacement, and reports honest shortfall.
- WeChat/GitHub mixed entries consume both slots; GitHub maximum cannot be bypassed by WeChat
  minimum reservation.
- Excluded count includes only candidates encountered while filling News and skipped solely by the
  GitHub cap; dedicated duplicates and candidates below a filled cutoff are excluded from the count.
- Artifact displays News GitHub actual/maximum/excluded. Cap-zero empty and nonempty branches retain
  honest `no_fresh_signals` / `partial` outcomes and explicit composition-exclusion copy.
- Entry titles retain the saved target URL. Hacker News attribution uses `discussion_url` with
  canonical fallback; X and WeChat attribution remain canonical.
- Current local archive produced five News entries with only one GitHub destination, replacing three
  higher-ranked excess GitHub links with non-GitHub stories.

## Limitations

- The repository-wide sweep is not green before/after this isolated change: existing
  `tests/test_discovery_runner.py` module functions request a nonexistent pytest `self` fixture;
  existing Papers save/category assertions fail; and Node/npm is unavailable in this shell. None of
  those files or behaviors are touched by this change. The directly affected and core adjacent test
  set is green.
- The local production briefing was intentionally generated without network collection so selection
  stayed deterministic. It is marked `partial` because no source reports were supplied; the check is
  evidence for composition, not a claim of a completed daily run.
- Live HN/WeChat/X network behavior was not required for this deterministic selector/rendering change.

## Review feedback

- Initial verify was `BLOCKED`: custom YAML values were not proven through the production runner,
  and the L1 diagram showed composition caps before cross-lane dedupe.
- The test now loads `github_news_max_items: 0` from YAML and asserts the generated artifact; the
  L1 flow now shows cross-lane dedupe before caps. The affected suite passes with 117 tests and 4
  subtests.
- Re-review verdict: PASS. Main briefing/signal-discovery Specs and L1/L2/L5 traceability were
  synchronized before archive.
