# Traceability — WeChat

| Requirement | Scenario | Code Anchor | Evidence | Status | Notes |
|-------------|----------|-------------|----------|--------|-------|
| Normalize Pasted Article URLs | Escaped shell separators | `normalize_wechat_url()` | `tests/test_wechat_collect.py::test_normalize_wechat_url` | verified | 根级参数化单测已覆盖常见粘贴变体 |
| Preserve Article Metadata | Successful article fetch | `extract_metadata()` + `build_markdown()` | `tests/test_research_item.py::test_fetch_article_writes_markdown_images_and_research_item_sidecar` | verified | fake browser 测试已断言标题、source URL、作者、发布时间与 sidecar metadata |
| Localize Referenced Images | Article contains downloadable images | `download_all_images()` + `replace_image_urls()` | `tests/test_research_item.py::test_fetch_article_writes_markdown_images_and_research_item_sidecar` + `tests/test_wechat_collect.py::test_replace_image_urls_handles_parentheses` | verified | fake download 测试已断言 images 文件落盘与 Markdown 相对路径重写 |
| Opt-In Live Validation | No live URLs configured | `tests/test_wechat_e2e_live.py` | 根级回归中 `1 skipped` | verified | 未配置 `WECHAT_E2E_URLS` 时会 clean skip |
| Expose WeChat via unified operator surface | Collect action dispatches to WeChat handler | `research/cli.py` + `collect_wechat_article()` | `tests/test_restructure_research_architecture.py::test_workspace_operator_surface_dispatches_collect_actions` | verified | WeChat 已通过统一入口暴露 |
| Persist article-side ResearchItem sidecar | Article markdown generated | `fetch_article()` + `build_wechat_item()` | `tests/test_research_item.py::test_fetch_article_writes_markdown_images_and_research_item_sidecar` | verified | fake browser / fake download 测试已断言 Markdown、images 与 `research-item.json` 同目录生成 |
