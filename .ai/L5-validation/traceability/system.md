# Traceability — System

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
| :---------- | :------- | :---------- | :------- | :----- | :---- |
| Runnable Documented Entrypoints | Follow workspace docs for CLI capabilities | `research/cli.py::build_parser` + `run_web_workspace()` | `tests/test_web_workspace.py::test_workspace_operator_surface_supports_local_web_entrypoint` | verified | 统一入口已新增 `web` 子命令 |
| Runnable Documented Entrypoints | Follow workspace docs for the local Web workspace | `workspace_web/server.py::serve_workspace` + `README.md` | `python3 -m research web` + `curl http://127.0.0.1:4173/` | verified | 文档启动路径已到达真实本地 Web 运行面 |
| Shared Local Archive Truth Across Surfaces | Browse local archive content from the Web workspace | `workspace_web/service.py::build_dashboard_overview` + `list_library_items()` | `tests/test_web_workspace.py::test_build_dashboard_overview_summarizes_local_archive_and_recent_briefings` + `tests/test_web_workspace.py::test_list_library_items_uses_local_filters_without_remote_collection` | verified | Dashboard / Library 都只消费本地 sidecar 与派生产物 |
| Shared Local Archive Truth Across Surfaces | Save a briefing from the Web workspace | `workspace_web/service.py::save_briefing` + `briefing/reports.py` | `tests/test_web_workspace.py::test_save_briefing_writes_output_and_marks_missing_sources` | verified | Web 保存保持 `output/briefing/` 边界，不改原始归档 |
