# Library 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/library/spec.md`
> 验证日期: 2026-08-13

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Unified ResearchItem | Load items from different sources | `library/items.py`, `library/storage.py` | `tests/test_research_item.py`, `tests/test_e2e_archive.py` | ✅ verified |
| Unified ResearchItem | Preserve first discovered_at / role / discovery method | `library/items.py` builders + JSONL persistence | `tests/test_realtime_signals.py`, `tests/test_research_item.py` | ✅ verified |
| Unified ResearchItem | Historical backfill does not invent discovery time | `library/items.py::backfill_output_tree` | `tests/test_realtime_signals.py`, `tests/test_research_item.py` | ✅ verified |
| Partial Metadata Is Allowed | Source omits optional fields | `library/items.py::ResearchItem` | `tests/test_research_item.py`, `tests/test_sidecar_schema_migration.py` | ✅ verified |
| Sidecar and Markdown Association | Open item detail | `workspace_web/service.py::get_library_item_detail` | `tests/test_service_e2e.py` | ✅ verified |
| Historical Backfill | Backfill an old archive | `library/items.py::backfill_output_tree` | `tests/test_research_item.py`, `tests/test_e2e_archive.py` | ✅ verified |
| Local Query | Filter local items | `library/query.py` | `tests/test_restructure_research_architecture.py`, `tests/test_library_query_datetime.py`, repository `output/` service round-trip, `web/test/fullstack.real_e2e.test.mjs` | ✅ verified |
| Resilient Sidecar Loading | One sidecar is malformed | `library/storage.py` | `tests/test_storage_and_jobs.py`, `tests/test_sidecar_schema_migration.py` | ✅ verified |

## Reverse traceability

pagination 与 safe preview 属于 Web presentation contract，记录在 `web-workspace`。
