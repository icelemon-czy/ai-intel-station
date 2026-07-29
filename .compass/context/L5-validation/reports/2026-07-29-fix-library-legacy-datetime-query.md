# Library Legacy Datetime Query 修复报告

## 结论

Library query 现在同时接受规范 ISO datetime 与已有 archive 中的
`YYYY-MM-DD HH:MM` minute-precision datetime。单条 malformed optional datetime
不会再让整个 query 或 Web request 崩溃：无 date filter 时 item 保持可见并稳定排在末尾，
有 date filter 时该 item 被隔离。

Main Library / Web Specs 已明确要求 local query、resilient loading 与 Library inspection，
因此本次没有修改 behavior source of truth，只修复 implementation 与 test gap。

## Red Evidence

修复前运行 public service 和新 regression：

```text
uv run --frozen python -m unittest tests.test_library_query_datetime
Ran 13 tests
FAILED (errors=3)
```

失败覆盖：

- private parser 不接受 `2026-04-02 08:31`。
- public `list_library_items()` 在真实 sidecar round-trip 中抛出 `ValueError`。
- malformed item 在无 filter query 的 sort 阶段抛出 `ValueError`。

repository `output/` 的直接 service call 同样复现
`ValueError: unparseable datetime '2026-04-02 08:31'`。

## Green Evidence

```text
uv run --frozen python -m unittest tests.test_library_query_datetime
Ran 14 tests — OK

uv run --frozen python -m unittest tests.test_service_e2e
Ran 26 tests — OK (9 sandbox socket tests skipped)

repository output service round-trip
items=20 total=30

bundled-node --test web/test/fullstack.real_e2e.test.mjs
5 passed, 0 failed, 0 skipped
```

real full-stack test 在允许 loopback socket 的环境运行；Library、detail、briefing preview/save
以及 collection request 均通过。

## Implementation Boundary

- `library/query.py` 在 Library boundary 兼容 system-produced legacy datetime。
- filter 与 sort 共用 item-side safe datetime selection。
- valid `published_at` 优先；invalid published 可 fallback 到 valid `updated_at`。
- invalid user filter 仍然报错，不被 item-side resilience 吞掉。

## Traceability

- Library `Local Query`：verified。
- Web Workspace `Library Search and Inspection`：verified。
- 对应 regression：`tests/test_library_query_datetime.py`。
