# Traceability — Research Query

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Query across multiple sources from local sidecars | Keyword matches items from github and papers | `library/storage.py` + `library/query.py` | `tests/test_restructure_research_architecture.py::test_query_research_items_supports_cross_source_keyword_source_and_optional_time_filters` | verified | 已确认查询只消费本地 sidecar |
| Support source filtering | Restrict results to github | `query_research_items(..., sources=...)` | 同上测试覆盖 source filter 断言 | verified | 兼容多来源后仍可单来源筛选 |
| Keep time filtering optional | No since/until returns full match set | `_matches_time_window()` | 同上测试覆盖 optional time behavior | verified | 未传时间条件不会误伤已有行为 |
| Apply explicit time window when provided | Since date removes older item | `_parse_datetime()` + `_matches_time_window()` | 同上测试覆盖 `since` 断言 | verified | 目前兼容 `YYYY-MM-DD` 与常见时间戳字符串 |
| Reuse historical archives without refetch | Existing Markdown can be backfilled then queried | `backfill_output_tree()` + `query_research_items()` | `tests/test_research_item.py::test_backfill_output_tree_writes_expected_sidecars` + `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_supports_query_briefing_and_backfill` | verified | 历史样例可直接进入 query / briefing 链路 |
