# Traceability — Papers

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| List Supported AI Categories | List categories | `CATEGORIES_HELP` + `main()` | 代码路径已确认 | untested | 当前会话未补跑 `research collect papers --list` smoke |
| Fetch Latest Papers by Category | Fetch one supported category | `fetch_papers_by_category()` | 代码路径已确认 | untested | 需要 mock arXiv 响应的单测 |
| Save One Markdown File per Paper | Save fetched papers | `paper_to_markdown()` + `save_papers()` | 代码路径已确认 | untested | 需要 tmp_path 文件系统测试 |
| Continue Across Category-Level Failures | Mixed category outcome | `fetch_papers_by_category()` exception branch | 代码中 `print` 后 `continue` | partial | 还缺显式 mixed-outcome 验证 |
| Expose papers via unified operator surface | Collect action dispatches to papers handler | `research/cli.py` + `collect_paper_categories()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | papers collect 已通过统一入口暴露 |
| Persist paper-side ResearchItem sidecar | Paper markdown generated | `save_papers()` + `build_paper_item()` | `tests/test_research_item.py::test_parse_existing_output_samples_into_research_items` | partial | sidecar 解析与 backfill 已测，仍缺 arXiv CLI smoke |