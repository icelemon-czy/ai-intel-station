# Implementation Tasks

## 1. Regression

- [x] 1.1 新增 test，验证 `fetch_papers_by_category()` 使用 HTTPS endpoint 并关闭 one-shot connection。
- [x] 1.2 确认 test 在旧 transport behavior 下失败，再由 connection fix 转绿。
- [x] 1.3 新增 transient timeout → retry、HTTP 429 → fallback 与 5xx retry exhaustion → fallback tests，并确认旧 code 先红。
- [x] 1.4 fallback fixture 断言 authors、arXiv id、PDF link 与 `max_results`，不接受空 metadata 或未截断虚假通过。

## 2. Runtime

- [x] 2.1 保留 `ARXIV_API` HTTPS endpoint，加入可靠 close header，不改变 query、response cap 或 Atom parsing。
- [x] 2.2 对 transient network/5xx 增加一次 bounded retry；per-attempt timeout 降为 15 秒。
- [x] 2.3 429 或 API retry exhaustion 时读取 official category Atom feed，并按 `max_results` 截断。
- [x] 2.4 解析 category feed 的 `dc:creator`，并从 abstract URL 恢复 id/PDF link。

## 3. Verification

- [x] 3.1 运行 Papers parser、discovery runner 与 scoped core regression。
- [x] 3.2 在非沙箱 network 下执行 one-paper smoke，并验证 Markdown + sidecar 落盘。
- [x] 3.3 执行 Papers-only discovery，确认 Papers source succeeded 且生成 fresh arXiv lane。
- [x] 3.4 完成只读 SDD verify、L5 traceability/report 与 archive。
