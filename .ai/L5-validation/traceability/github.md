# Traceability — GitHub

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Save Repository Snapshots as Markdown | Fetch one repository | `fetch_repo()` + `save_repo()` | 代码路径已确认 | untested | 仍需 `gh` smoke 或 subprocess mock 测试 |
| Save Search Results as Markdown | Search by query | search branch + `save_search_results()` | 代码路径已确认 | untested | 当前仍缺真实 `gh search` 自动化验证 |
| Include Open Issues in Repository Snapshots | Repository has open issues | `fetch_repo()` | 代码中会拉取 issues | untested | `--issues` 语义与实现仍需后续澄清 |
| Surface GitHub CLI Failures | `gh` returns non-zero | `run_gh()` | 代码显式 `raise RuntimeError` | partial | 还缺失败路径测试或实际失败复现记录 |
| Expose GitHub via unified operator surface | Collect action dispatches to GitHub handler | `research/cli.py` + `collect_github_targets()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | GitHub collect 已通过统一入口暴露 |
| Persist repo-side ResearchItem sidecar | Repository snapshot generated | `save_repo()` + `build_github_repo_item()` | `tests/test_research_item.py::test_build_github_repo_item_normalizes_repository_metadata` | partial | builder 已测，仍缺真实 `gh` smoke |
| Persist search-side ResearchItems JSONL | Search results generated | `build_github_search_items()` + parser/backfill | `tests/test_research_item.py::test_parse_existing_output_samples_into_research_items` | partial | 解析与 backfill 已测，仍缺真实 `gh search` 命令级验证 |