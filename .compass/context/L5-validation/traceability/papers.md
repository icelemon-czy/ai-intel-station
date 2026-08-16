# Papers 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/papers/spec.md`
> 验证日期: 2026-08-16

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Supported Category Discovery | List categories | `collect/papers.py::AI_CATEGORIES` | `tests/test_l3_subspec_e2e.py` | ✅ verified |
| Latest Papers by Category | Fetch one category | `collect/papers.py::fetch_papers_by_category` | `tests/test_l3_subspec_remaining_e2e.py`, `tests/test_papers_atom_parse.py`, `tests/test_l3_http_e2e.py`; 2026-08-15 live one-paper + Papers-only discovery smoke | ✅ verified |
| One Artifact per Paper | Persist fetched papers | `collect/papers.py::save_papers` | `tests/test_research_item.py`, `tests/test_save_papers.py` | ✅ verified |
| Category Failure Isolation | Mixed category result | `research/cli.py`, `collect/papers.py`, `research/discovery/runner.py` | `tests/test_l3_subspec_e2e.py`, `tests/test_discovery_runner.py` | ✅ verified |
| Papers Evidence Role | Fresh Paper enters only dedicated arXiv section and cannot fill realtime source quota | `library/items.py`, `briefing/signals.py::select_daily_briefing` | `tests/test_realtime_signals.py` dedicated composition/latest publication/stale exclusion assertions | ✅ verified |

## Reverse traceability

未发现 core Papers behavior 缺少主 Spec。
