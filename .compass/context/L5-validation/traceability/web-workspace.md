# Web Workspace 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/web-workspace/spec.md`
> 验证日期: 2026-07-29

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Stable Workspace Navigation | Switch away from Library and return | `web/src/App.jsx` | `web/test/autoRefresh.react.test.mjs` | ✅ verified |
| Dashboard Uses Local Truth | Open Dashboard with an empty archive | `workspace_web/service.py::build_dashboard_overview` | `tests/test_service_e2e.py` | ✅ verified |
| Library Search and Inspection | Inspect a selected item | `workspace_web/service.py`, `web/src/App.jsx` | `tests/test_service_e2e.py`, `tests/test_library_query_datetime.py`, repository `output/` service round-trip, `web/test/fullstack.real_e2e.test.mjs` | ✅ verified |
| Library Search and Inspection | Reject an unknown preview path | `workspace_web/service.py::read_item_markdown` | `tests/test_service_e2e.py` | ✅ verified |
| Explicit Local File Actions | Operator needs the local file | `web/src/App.jsx` | `tests/test_web_workspace.py` | ✅ verified |
| Briefing Preview and Save | Preview then save | `workspace_web/service.py` | `tests/test_service_e2e.py` | ✅ verified |
| Manual Source Collection | Complete a manual collect | `workspace_web/service.py::run_collect` | `tests/test_service_e2e.py`, `tests/test_web_workspace.py` | ✅ verified |
| Non-Blocking Auto Refresh | Polling request fails | `web/src/autoRefresh.js`, `web/src/App.jsx` | `web/test/autoRefresh.test.mjs`, `web/test/autoRefresh.react.test.mjs` | ✅ verified |
| Daily Discovery Action | Trigger daily discovery from Dashboard | `web/src/DailyDiscoveryCard.jsx`, `workspace_web/service.py` | `web/test/discoveryCard.*.test.mjs`, `tests/test_discovery_web.py` | ✅ verified |

## Reverse traceability

Web 明确不承诺 generic job history、schedule controls 或 dashboard job badges；source 中的 “What is not here yet” 与主 Spec boundary 一致。

`web/test/fullstack.contract.test.mjs` 从 built bundle 提取全部 frontend API literal，
并用一一对应的 method、valid dynamic input 与 isolated output fixture 请求 real backend。
因此 GET / POST route、detail / preview parameter 与 route-specific error 均不会被
method-insensitive path sweep 冒充为 integration evidence。
