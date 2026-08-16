# GitHub 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/github/spec.md`
> 验证日期: 2026-08-16

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Repository Snapshot | Collect one repository | `collect/github.py::save_repo` | `tests/test_research_item.py`, `tests/test_e2e_archive.py` | ✅ verified |
| Repository Search Snapshot | Recency order + metadata + real Path | `collect/github.py::save_search_results` | `tests/test_realtime_signals.py`, `tests/test_research_item.py` | ✅ verified |
| Optional Issue Coverage | Collect with issues enabled | `collect/github.py` | `tests/test_l3_subspec_remaining_e2e.py` | ✅ verified |
| GitHub Sidecars | Load a collected repository in Library | `library/items.py`, `library/storage.py` | `tests/test_e2e_archive.py` | ✅ verified |
| Explicit GitHub CLI Failure | GitHub CLI returns non-zero | `collect/github.py::run_gh` | `tests/test_l3_subspec_e2e.py`, `tests/test_service_e2e.py` | ✅ verified |
| GitHub Evidence Role | Fresh repo enters only dedicated GitHub section and cannot fill realtime source quota | `library/items.py`, `briefing/signals.py::select_daily_briefing` | `tests/test_realtime_signals.py` dedicated composition, created-first and published fallback assertions | ✅ verified |

## Reverse traceability

未发现 core GitHub behavior 缺少主 Spec。
