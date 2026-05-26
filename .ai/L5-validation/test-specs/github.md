# Test Specs — GitHub Gaps

## Repository Snapshot Generation

1. **covered: save_repo happy path**
   Evidence: `tests/test_research_item.py::test_save_repo_writes_markdown_and_research_item_sidecar`
   Covers: `README.md`、stars、language、URL、issues、`research-item.json` 同目录 sidecar。

2. **remaining gap: error path**
   Input: mock `gh` 返回非零并带 stderr。
   Expect: `run_gh()` 抛 `RuntimeError`，错误信息包含 stderr。

## Search Snapshot Generation

1. **covered: search happy path**
   Evidence: `tests/test_research_item.py::test_save_search_results_writes_markdown_and_jsonl_sidecar`
   Covers: `search.md`、query 空格目录名、`research-items.jsonl`、query / owner / repo / stars metadata。

2. **historical note**
   Input: `--search` 模式下 mock 返回 2 个 repo 结果。
   Expect: 写出 `search.md`，目录名与 query 对应。

## Invalid Target Handling

1. **error path**
   Input: repo 模式传入不含 `/` 的 target。
   Expect: 打印 skip 提示，不尝试写 repo 输出目录。
