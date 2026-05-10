# Traceability — WeChat

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Normalize Pasted Article URLs | Escaped shell separators | `normalize_wechat_url()` | `tests/test_wechat_collect.py::test_normalize_wechat_url` | verified | 根级参数化单测已覆盖常见粘贴变体 |
| Preserve Article Metadata | Successful article fetch | `extract_metadata()` + `build_markdown()` | 代码路径已确认 | partial | 还缺显式断言标题与 source URL 的 Markdown 测试 |
| Localize Referenced Images | Article contains downloadable images | `download_all_images()` + `replace_image_urls()` | `tests/test_wechat_collect.py::test_replace_image_urls_handles_parentheses` | partial | 链接重写已测，真实下载链路仍主要靠 live e2e |
| Opt-In Live Validation | No live URLs configured | `tests/test_wechat_e2e_live.py` | 根级回归中 `1 skipped` | verified | 未配置 `WECHAT_E2E_URLS` 时会 clean skip |
| Expose WeChat via unified operator surface | Collect action dispatches to WeChat handler | `research/cli.py` + `collect_wechat_article()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | WeChat 已通过统一入口暴露 |
| Persist article-side ResearchItem sidecar | Article markdown generated | `fetch_article()` + `build_wechat_item()` | `tests/test_research_item.py` builder / backfill 覆盖 | partial | 共享层已验证，仍缺浏览器环境下的命令级 smoke |
