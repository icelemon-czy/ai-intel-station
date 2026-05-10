# Test Specs — GitHub Gaps

## Repository Snapshot Generation

1. **happy path**
   Input: mock `gh repo view` 和 `gh issue list` 返回固定 JSON。
   Expect: `save_repo()` 写出 `README.md`，包含 stars、language、URL、issues。
   Setup: monkeypatch `run_gh()`，用 `tmp_path` 作为输出目录。

2. **error path**
   Input: mock `gh` 返回非零并带 stderr。
   Expect: `run_gh()` 抛 `RuntimeError`，错误信息包含 stderr。

## Search Snapshot Generation

1. **happy path**
   Input: `--search` 模式下 mock 返回 2 个 repo 结果。
   Expect: 写出 `search.md`，目录名与 query 对应。

2. **edge case**
   Input: query 包含空格。
   Expect: 输出目录按当前规则替换为空格连字符，不丢结果。

## Invalid Target Handling

1. **error path**
   Input: repo 模式传入不含 `/` 的 target。
   Expect: 打印 skip 提示，不尝试写 repo 输出目录。