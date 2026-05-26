# Test Specs — WeChat Gaps

## Preserve Article Metadata

1. **covered: fetch_article happy path**
   Evidence: `tests/test_research_item.py::test_fetch_article_writes_markdown_images_and_research_item_sidecar`
   Covers: fake browser HTML 下生成 Markdown 顶部标题、source URL、作者、发布时间，以及 `research-item.json` metadata。

2. **historical note**
   Input: 最小 article HTML，包含标题、公众号名、发布时间、正文。
   Expect: 生成 Markdown 顶部包含标题和 source URL。
   Setup: 直接调用 `extract_metadata()` / `build_markdown()`，不走网络。

3. **remaining gap: edge case**
   Input: 缺失发布时间但存在其他字段的 HTML。
   Expect: Markdown 仍生成，缺失字段有稳定降级行为，不抛异常。

## Localize Referenced Images

1. **covered: image localization happy path**
   Evidence: `tests/test_research_item.py::test_fetch_article_writes_markdown_images_and_research_item_sidecar`
   Covers: fake download 成功时 `images/` 文件生成，Markdown 图片链接改为相对路径。

2. **historical note**
   Input: 含两张图片 URL 的正文 HTML，mock 下载成功。
   Expect: `images/` 下生成两个文件，Markdown 链接被替换成相对路径。

3. **remaining gap: error path**
   Input: 一张图片下载失败，一张成功。
   Expect: 成功图片被重写，失败图片保留可诊断信息或稳定回退行为。

## Live Validation

1. **skip path**
   Input: `WECHAT_E2E_URLS` 为空。
   Expect: `test_live_articles_end_to_end` 标记为 skipped。
