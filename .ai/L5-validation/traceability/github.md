# Traceability — GitHub

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Save Repository Snapshots as Markdown | Fetch one repository | `fetch_repo()` + `save_repo()` | `tests/test_research_item.py::test_save_repo_writes_markdown_and_research_item_sidecar` | partial | 落盘与 Markdown 内容已测；真实 `gh` smoke 仍可作为外部依赖验证补充 |
| Save Search Results as Markdown | Search by query | search branch + `save_search_results()` | `tests/test_research_item.py::test_save_search_results_writes_markdown_and_jsonl_sidecar` | partial | 搜索结果落盘与 query 目录命名已测；真实 `gh search` smoke 仍可作为外部依赖验证补充 |
| Include Open Issues in Repository Snapshots | Repository has open issues | `fetch_repo()` | 代码中会拉取 issues | untested | `--issues` 语义与实现仍需后续澄清 |
| Surface GitHub CLI Failures | `gh` returns non-zero | `run_gh()` | 代码显式 `raise RuntimeError` | partial | 还缺失败路径测试或实际失败复现记录 |
| Expose GitHub via unified operator surface | Collect action dispatches to GitHub handler | `research/cli.py` + `collect_github_targets()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | GitHub collect 已通过统一入口暴露 |
| Persist repo-side ResearchItem sidecar | Repository snapshot generated | `save_repo()` + `build_github_repo_item()` | `tests/test_research_item.py::test_save_repo_writes_markdown_and_research_item_sidecar` | verified | tmp_path 文件系统测试已断言 `README.md` 与 `research-item.json` 同目录生成及 sidecar 关键字段 |
| Persist search-side ResearchItems JSONL | Search results generated | `save_search_results()` + `build_github_search_items()` | `tests/test_research_item.py::test_save_search_results_writes_markdown_and_jsonl_sidecar` | verified | tmp_path 文件系统测试已断言 `search.md`、`research-items.jsonl`、query metadata 与 JSONL 内容 |
