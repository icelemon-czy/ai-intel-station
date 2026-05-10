# Test Specs — WeChat Gaps

## Preserve Article Metadata

1. **happy path**
   Input: 最小 article HTML，包含标题、公众号名、发布时间、正文。
   Expect: 生成 Markdown 顶部包含标题和 source URL。
   Setup: 直接调用 `extract_metadata()` / `build_markdown()`，不走网络。

2. **edge case**
   Input: 缺失发布时间但存在其他字段的 HTML。
   Expect: Markdown 仍生成，缺失字段有稳定降级行为，不抛异常。

## Localize Referenced Images

1. **happy path**
   Input: 含两张图片 URL 的正文 HTML，mock 下载成功。
   Expect: `images/` 下生成两个文件，Markdown 链接被替换成相对路径。

2. **error path**
   Input: 一张图片下载失败，一张成功。
   Expect: 成功图片被重写，失败图片保留可诊断信息或稳定回退行为。

## Live Validation

1. **skip path**
   Input: `WECHAT_E2E_URLS` 为空。
   Expect: `test_live_articles_end_to_end` 标记为 skipped。