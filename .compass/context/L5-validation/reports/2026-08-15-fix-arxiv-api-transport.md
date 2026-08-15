# Validation Report: fix-arxiv-api-transport

**Date**: 2026-08-15
**Change**: `.compass/context/L3-specs/archive/fix-arxiv-api-transport/`
**Status**: PASS

## Root cause evidence

- Sandbox category collect failed at DNS boundary (`Errno 8`), so it could not distinguish query
  correctness from network policy.
- An approved network smoke resolved the host, but Python `urllib` intermittently timed out reading
  the arXiv search API and then received HTTP 429 on retry. The same query succeeded through `curl`.
- arXiv documents both the search API and an official per-category Atom feed. The latter returned a
  current 2026-08-14 `cs.AI` feed and became the bounded fallback rather than a scraped third-party
  source.

## Executed checks

| Command / check | Result |
|---|---|
| Pre-fix connection-boundary regression | RED: request lacked the required one-shot close semantics |
| Pre-fix transient timeout regression | RED: original collector performed one attempt only |
| Pre-fix HTTP 429 fallback regression | RED: original collector had no alternate official transport |
| Pre-fix official-feed metadata regression | RED: `dc:creator` produced empty authors and no derived PDF URL |
| `.venv/bin/python -m pytest -q tests/test_papers_atom_parse.py tests/test_save_papers.py` | 19 passed |
| `.venv/bin/python -m pytest -q tests/test_papers_atom_parse.py` (post-review 5xx exhaustion regression) | 16 passed |
| `.venv/bin/python -m pytest -q tests/test_papers_atom_parse.py tests/test_save_papers.py tests/test_research_item.py::test_save_papers_writes_markdown_and_research_item_sidecar` (after fallback truncation assertion) | 20 passed |
| `.venv/bin/python -m pytest -q tests/test_papers_atom_parse.py tests/test_save_papers.py tests/test_restructure_research_architecture.py tests/test_l3_subspec_remaining_e2e.py::L3PapersFetchLatestSubprocessTests` (post-review) | 29 passed |
| `.venv/bin/python -m unittest -v tests.test_discovery_runner` | 15 passed |
| `.venv/bin/python -m pytest -q tests -m 'not wechat' --ignore=tests/test_discovery_runner.py --ignore=tests/test_web_workspace.py` | 380 passed, 24 skipped, 16 deselected, 4 subtests passed |
| `.venv/bin/python -m pytest -q tests/test_l3_requirements.py tests/test_l3_policy_meta.py` | 7 passed |
| scoped `git diff --check` | exit 0 |
| Approved live `research collect papers cs.AI --max 1` to `/private/tmp/ai-intel-arxiv-metadata-smoke-20260815` | exit 0; search timeout/429 isolated; official Atom fallback saved one Markdown + sidecar |
| Saved smoke metadata inspection | title, Rachel Lawrence / Jacqueline Maasch, `published_at=2026-08-14T00:00:00-04:00`, canonical abstract URL and PDF URL present |
| Approved live `.venv/bin/python -m research discover --source papers` | exit 0; `papers: succeeded=3 skipped=0 failed=0`; briefing `daily-2026-08-15-3.md` has arXiv expected=1 / actual=1 / missing=0 |

## Contract evidence checked

- Search request remains HTTPS, retains the existing query shape and identifies/closes the
  one-shot client connection.
- Transient network/5xx failure receives one bounded retry with 15-second per-attempt timeout.
- HTTP 429 or exhausted search attempts switches to `https://rss.arxiv.org/atom/<category>` once.
- Both transports retain the 5 MiB response cap; fallback results are sliced to `max_results`.
- Official feed `dc:creator`, OAI id and canonical abstract link produce non-empty authors, arXiv id
  and PDF URL.
- Category isolation remains intact in the discovery runner.

## Broad-suite disclosure

An unfiltered `pytest -q tests -m 'not wechat'` run was **not green**: 485 passed, 27 skipped,
16 deselected, 15 errors and 3 failures. The 15 errors are existing unittest-style functions in
`tests/test_discovery_runner.py` collected by pytest without a `self` fixture; that module passes
15/15 through its intended unittest runner. Two apparent Papers/service failures passed immediately
when rerun in isolation, showing cross-suite state pollution. The third failure is `npm` missing in
this shell. The scoped broad command above excludes those two known runner/environment files and is
green. No failed command is represented as successful evidence.

## Limitations

- arXiv search API availability and shared-IP throttle remain external. The fix provides bounded
  resilience using a second official source; if both official endpoints fail, the category still
  reports failure honestly.
- The official category feed is daily rather than an arbitrary search endpoint, which is sufficient
  for the product's `Latest Papers by Category` daily discovery contract.
- Direct `research collect papers` remote-failure exit-code semantics are a separate operator-surface
  issue and were not changed here.

## Review feedback

- 首轮 verify `BLOCKED`：缺少 5xx retry 与 retry exhaustion 后 official-feed success 的
  deterministic anti-overfit assertion。新增 `503 → 502 → official feed` test，精确断言两次
  search URL、一次 fallback URL、`Retry-After: 90` capped 为 30 秒且 fallback 成功；targeted
  suite 16/16 通过。
- re-review verdict: `PASS`。Reviewer 确认原 blocker 已闭合，且 HTTPS/close/timeout、timeout
  retry、429 fallback、5xx exhaustion、delay cap、fallback truncation/metadata、category isolation
  与 live artifact/discovery evidence 均满足验证要求。
