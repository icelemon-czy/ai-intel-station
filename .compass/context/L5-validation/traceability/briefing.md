# Briefing 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/briefing/spec.md`
> 验证日期: 2026-08-15

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Local Briefing Input | Generate from local archive | `briefing/main.py`, `library/query.py` | `tests/test_restructure_research_architecture.py`, `tests/test_briefing_reports.py` | ✅ verified |
| Digest and Reading List Modes | Select a mode | `briefing/reports.py` | `tests/test_briefing_reports.py` | ✅ verified |
| Derived Output Boundary | Save briefing | `publish/obsidian.py` | `tests/test_obsidian_publish.py`, `tests/test_service_e2e.py` | ✅ verified |
| Explicit Source Gaps | Requested source has no items | `briefing/reports.py` | `tests/test_restructure_research_architecture.py`, `tests/test_l3_subspec_e2e.py` | ✅ verified |
| Preview and Listing | Preview without saving | `workspace_web/service.py::preview_briefing`, `briefing/main.py` | `tests/test_service_e2e.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Distinct Target and Signal Attribution Links | HN title target + discussion attribution, historical fallback, X/WeChat canonical and dry-run maximum | `briefing/signals.py::_entry_markdown`, `research/discovery/runner.py::generate_briefing` | `tests/test_realtime_signals.py` source-native link + dry-run assertions | ✅ verified |
| Daily Signal Briefing | Default 5 News/up to 2 optional WeChat/up to 1 GitHub destination + 1 GitHub + 1 arXiv composition | `briefing/signals.py::select_daily_briefing`, `research/discovery/runner.py::generate_briefing` | `tests/test_realtime_signals.py` cap/replacement/shortfall selector + real production generate assertions | ✅ verified |
| Daily Signal Briefing | Optional WeChat failure outcome matrix and X/only-WeChat boundaries | `briefing/signals.py::_source_status_lines`, `research/discovery/runner.py::generate_briefing` | `tests/test_realtime_signals.py` renderer + parametrized production-path matrix | ✅ verified |
| Daily Signal Briefing | Required lane shortfall + dedicated corroboration confidence | `briefing/signals.py` | `tests/test_realtime_signals.py` no-failure shortfall, low/medium/high and grouped renderer assertions | ✅ verified |
| Honest Empty Signal Result | complete/incomplete empty + legacy cap + selective omission | `briefing/signals.py`, `research/discovery/runner.py` | `tests/test_realtime_signals.py`, `tests/test_discovery_runner.py` | ✅ verified |
| Honest Empty Signal Result | quota bounds/type/relation/source validation, GitHub-cap exclusion and config migration | `research/discovery/config.py`, `briefing/signals.py` | `tests/test_realtime_signals.py` production non-default YAML, explicit-empty/cap-zero, integer, conflict and migration assertions | ✅ verified |
| Source Coverage in Daily Briefing | Any attempted enabled source failure | `research/discovery/runner.py`, `briefing/signals.py` | `tests/test_realtime_signals.py` renderer matrix + production attempted-X failure assertion | ✅ verified |

## Reverse traceability

未发现 core Briefing behavior 缺少主 Spec。Web consumer 对 structured outcome 的展示追溯在
`daily-discovery.md` 与 2026-08-13 validation report。
