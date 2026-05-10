# Traceability — Archive Output

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Preserve original raw archive roots | GitHub / papers / wechat raw outputs remain unchanged | `collect/github.py` / `collect/papers.py` / `collect/wechat.py` output constants | `tests/test_restructure_research_architecture.py` | verified | 本轮迁移未改变原始抓取目录命名 |
| Write derived briefings into a separate tree | Digest and reading list land under `output/briefing/` | `publish/obsidian.py` + `briefing/reports.py` | `tests/test_restructure_research_architecture.py::test_digest_and_reading_list_reports_write_obsidian_friendly_markdown` | verified | 派生产物边界已落定 |
| Reuse historical markdown via sidecar backfill | Existing archive can be lifted into library layer | `library/items.py` + `backfill_output_tree()` | `tests/test_research_item.py::test_backfill_output_tree_writes_expected_sidecars` + `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_supports_query_briefing_and_backfill` | verified | 不要求重新抓取才能查询或出简报 |
