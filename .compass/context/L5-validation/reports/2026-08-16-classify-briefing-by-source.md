# Validation Report: classify-briefing-by-source

**Date**: 2026-08-16
**Change**: `.compass/context/L3-specs/archive/classify-briefing-by-source/`
**Status**: PASS

## Executed checks

| Command | Result |
|---|---|
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py tests/test_restructure_research_architecture.py tests/test_briefing_marker.py` | 110 passed, 4 subtests passed |
| `UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv run --frozen --extra dev python -m unittest tests.test_discovery_runner` | 15 passed; dry-run composition=`3 Hacker News + WeChat optional maximum=2 (minimum=0) + 0 X + 1 GitHub + 1 arXiv` |
| Main Spec structure check (Requirement ≥1 Scenario, WHEN/THEN present, no duplicate Requirement names) | briefing 9 / signal-discovery 5 / daily-discovery 8 / github 6 / papers 5；无缺失 Scenario |

## Contract evidence checked

- Default quota selector returns 3 Hacker News + up to 2 WeChat + 1 GitHub + 1 arXiv. HN stories whose canonical target is github.com stay in the Hacker News section and are not recategorized as GitHub news.
- Optional WeChat maximum truncates WeChat only. Missing Hacker News is reported as Hacker News shortfall (`partial`); there is no user-visible News missing count.
- Exact URL/title ownership is `papers > github > hackernews > wechat > x`. A dedicated GitHub entry owns a matching HN signal as corroboration; a distinct HN GitHub-target story can still fill Hacker News.
- Existing `news_items=5` without `hackernews_items` migrates to `hackernews_items=5`. Existing `github_news_max_items` is ignored, including invalid values in non-signals modes and a production YAML path with `github_news_max_items: 0`.
- Artifact headings are arXiv / GitHub / Hacker News / WeChat. `x_items=0` does not render an X section. Dry-run prints configured source maxima and does not invent GitHub destination actual/excluded.
- Daily Skill contract asserts source grouping, forbids reporting GitHub destination excluded counts, and no longer requires a News lane.
- GitHub/Paper evidence still cannot fill Hacker News / WeChat / X quotas; they only occupy their dedicated sections.

## Limitations

- Live HN / WeChat / X network collection was not required; selector, config, renderer and production `generate_briefing` paths used local fixtures.
- Codex 本机 automation prompt 若仍写 “5 News”，不在本仓库内；归档后如仍存在需另改。
- Repository-wide pytest was not re-used as a pass/fail gate. Prior adjacent sweep had unrelated `test_l3_http_e2e` timeout and `test_web_workspace` missing `npm`. This change does not touch those files.

## Review feedback

- Main Agent completed verify because this platform has no `sdd-reviewer` subagent.
- Tightened a leftover dry-run assertion that previously accepted either `3` or `5` Hacker News; the production config under test now must print `5 Hacker News`.
- Skill contract now also asserts the absence of destination-excluded / `5 News` / `github_news_max_items` copy.
- Verdict: PASS. Delta specs merged into main briefing / signal-discovery / daily-discovery / github / papers Specs; L1/L2/L5 synchronized before archive.
