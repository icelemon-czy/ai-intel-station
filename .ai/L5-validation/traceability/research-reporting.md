# Traceability — Research Reporting

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Generate digest markdown from local query results | Digest report written under output tree | `briefing/reports.py` + `write_digest_report()` | `tests/test_restructure_research_architecture.py::test_digest_and_reading_list_reports_write_obsidian_friendly_markdown` | verified | 已确认报告 writer 可用 |
| Generate reading list markdown from local query results | Reading list report includes checkbox entries | `build_reading_list_markdown()` | 同上测试覆盖 reading-list 输出断言 | verified | 满足 Obsidian 可勾选阅读清单场景 |
| Surface partial success explicitly | Missing requested source still yields report with coverage note | `_coverage_note()` | `tests/test_restructure_research_architecture.py::test_digest_reports_partial_success_when_a_requested_source_is_missing` | verified | 输出正文中明确包含 `Missing sources: ...` |
| Keep derived reports separate from raw archives | Report path uses `output/briefing/*` | `publish/obsidian.py` | `tests/test_restructure_research_architecture.py::test_digest_and_reading_list_reports_write_obsidian_friendly_markdown` | verified | 未覆盖原始 `output/github|papers|wechat` |
