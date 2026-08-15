# Briefing 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/briefing/spec.md`
> 验证日期: 2026-08-14

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Local Briefing Input | Generate from local archive | `briefing/main.py`, `library/query.py` | `tests/test_restructure_research_architecture.py`, `tests/test_briefing_reports.py` | ✅ verified |
| Digest and Reading List Modes | Select a mode | `briefing/reports.py` | `tests/test_briefing_reports.py` | ✅ verified |
| Derived Output Boundary | Save briefing | `publish/obsidian.py` | `tests/test_obsidian_publish.py`, `tests/test_service_e2e.py` | ✅ verified |
| Explicit Source Gaps | Requested source has no items | `briefing/reports.py` | `tests/test_restructure_research_architecture.py`, `tests/test_l3_subspec_e2e.py` | ✅ verified |
| Preview and Listing | Preview without saving | `workspace_web/service.py::preview_briefing`, `briefing/main.py` | `tests/test_service_e2e.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Daily Signal Briefing | Default 5 News/2 WeChat + 1 GitHub + 1 arXiv composition | `briefing/signals.py::select_daily_briefing`, `research/discovery/runner.py::generate_briefing` | `tests/test_realtime_signals.py` public selector + real production generate assertions | ✅ verified |
| Daily Signal Briefing | Required lane shortfall + dedicated corroboration confidence | `briefing/signals.py` | `tests/test_realtime_signals.py` no-failure shortfall, low/medium/high and grouped renderer assertions | ✅ verified |
| Honest Empty Signal Result | complete/incomplete empty + legacy cap + selective omission | `briefing/signals.py`, `research/discovery/runner.py` | `tests/test_realtime_signals.py`, `tests/test_discovery_runner.py` | ✅ verified |
| Honest Empty Signal Result | quota bounds/type/relation/source validation | `research/discovery/config.py` | `tests/test_realtime_signals.py` explicit-empty, integer, conflict and viability assertions | ✅ verified |
| Source Coverage in Daily Briefing | Any attempted enabled source failure | `research/discovery/runner.py`, `briefing/signals.py` | `tests/test_realtime_signals.py` renderer matrix + production attempted-X failure assertion | ✅ verified |

## Reverse traceability

未发现 core Briefing behavior 缺少主 Spec。Web consumer 对 structured outcome 的展示追溯在
`daily-discovery.md` 与 2026-08-13 validation report。
