# Traceability — Research Operations

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Provide one workspace operator surface | Root command exposes collect / query / briefing / backfill | `research/cli.py` + `build_parser()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_supports_query_briefing_and_backfill` | verified | 统一入口已覆盖 4 类动作 |
| Dispatch collect actions by source | GitHub / papers / WeChat route to their handlers | `collect_github_targets()` / `collect_paper_categories()` / `collect_wechat_article()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | 子命令已绑定到业务层 handler |
| Continue partial briefing results | Requested sources incomplete still yields report | `generate_briefing()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_continues_with_partial_briefing_results` | verified | 部分成功语义保留在统一入口层 |