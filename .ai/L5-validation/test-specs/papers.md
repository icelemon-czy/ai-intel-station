# Test Specs — Papers Gaps

## Category Listing

1. **happy path**
   Input: `--list`
   Expect: 输出包含 `cs.AI`、`cs.LG` 等支持类别。

## Fetch Latest Papers by Category

1. **happy path**
   Input: mock arXiv Atom XML，包含 2 篇 `cs.AI` 论文。
   Expect: `fetch_papers_by_category()` 返回 2 条结构化 paper dict。

2. **error path**
   Input: 一个未知类别。
   Expect: 打印 unknown category warning，不抛异常。

## Save Markdown Files

1. **covered: save_papers happy path**
   Evidence: `tests/test_research_item.py::test_save_papers_writes_markdown_and_research_item_sidecar`
   Covers: `arXiv-cs.AI/01-*.md` 和同目录 `<stem>.research-item.json`，并断言 paper title、authors、summary、published、categories、PDF metadata。

2. **historical note**
   Input: 2 条 paper dict，`tmp_path` 作为输出目录。
   Expect: `arXiv-cs.AI/` 下生成 `01-*.md` 和 `02-*.md`。

3. **remaining gap: edge case**
   Input: 标题含特殊字符。
   Expect: 文件名被安全化，但 Markdown 标题保留原始含义。

## Mixed Category Outcome

1. **partial failure path**
   Input: 一个类别请求抛异常，另一个类别返回有效 XML。
   Expect: 失败类别被报告，成功类别仍写入文件。
