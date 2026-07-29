# Briefing 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/briefing/spec.md`
> 验证日期: 2026-07-25

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Local Briefing Input | Generate from local archive | `briefing/main.py`, `library/query.py` | `tests/test_restructure_research_architecture.py`, `tests/test_briefing_reports.py` | ✅ verified |
| Digest and Reading List Modes | Select a mode | `briefing/reports.py` | `tests/test_briefing_reports.py` | ✅ verified |
| Derived Output Boundary | Save briefing | `publish/obsidian.py` | `tests/test_obsidian_publish.py`, `tests/test_service_e2e.py` | ✅ verified |
| Explicit Source Gaps | Requested source has no items | `briefing/reports.py` | `tests/test_restructure_research_architecture.py`, `tests/test_l3_subspec_e2e.py` | ✅ verified |
| Preview and Listing | Preview without saving | `workspace_web/service.py::preview_briefing`, `briefing/main.py` | `tests/test_service_e2e.py`, `tests/test_cli_e2e.py` | ✅ verified |

## Reverse traceability

未发现 core Briefing behavior 缺少主 Spec。
