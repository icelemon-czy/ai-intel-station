# 测试审查报告: add-research-operator-surface

## 本次审查目标
- 类型: change
- 名称: add-research-operator-surface
- 优先级来源: P1 pending-review
- 队列剩余: 4 项未审，下次调用将审查 separate-legacy-compatibility-layer

## 测试规范
- 测试框架: pytest
- 测试目录: `tests/`
- 规范命令: `uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_wechat_collect.py`
- 本次相关测试: `python3 -m pytest tests/test_restructure_research_architecture.py`
- 运行器: `/opt/homebrew/opt/python@3.10/bin/python3.10`

## 执行结果
- 测试运行: ✅ 全绿（8 passed）
- 异常标记: 无
- 审查范围: `.ai/L3-specs/changes/add-research-operator-surface/specs/`

## 主表

| # | Req | Scenario | Spec THEN | 测试函数 | 测试文件:行 | 实际 assertion | 调用链验证 | 反模式 | 反向推理 | 结论 |
|---|-----|----------|-----------|----------|-------------|---------------|------------|--------|----------|------|
| 1 | Unified Workspace Command Surface | Collect from GitHub through the workspace surface | command reaches GitHub collect implementation and writes artifacts under `output/github/` | `test_workspace_operator_surface_dispatches_collect_actions` | `test_restructure_research_architecture.py:203` | `main(["collect", "github", ...]) == 0`; `calls == [("github", (...))]` | ✅ 真实调用 `main()` → `collect_github_targets()` | ✅ 全通过 | ✅ 删 collect_github_targets 会红 | ✅ |
| 2 | Unified Workspace Command Surface | Collect from papers or WeChat through the workspace surface | command reaches corresponding collect without requiring a source-specific top-level script path | `test_workspace_operator_surface_dispatches_collect_actions` | `test_restructure_research_architecture.py:203` | `main(["collect", "papers", ...]) == 0`; `main(["collect", "wechat", ...]) == 0`; calls tuples match | ✅ 真实调用 `main()` → `collect_paper_categories()` / `collect_wechat_article()` | ✅ 全通过 | ✅ 删对应 handler 会红 | ✅ |
| 3 | Workspace Query And Briefing Actions | Query local research items through the workspace surface | command loads local sidecars and prints result view without remote fetch | `test_workspace_operator_surface_supports_query_briefing_and_backfill` | `test_restructure_research_architecture.py:234` | `"Claude Code" in query_stdout`; `"Agent Harness Benchmark" in query_stdout` | ✅ 真实调用 `main()` → `query_research_items()` | ✅ 全通过 | ✅ 删 query_research_items 会红 | ✅ |
| 4 | Workspace Query And Briefing Actions | Generate a briefing through the workspace surface | command writes derived Markdown under `output/briefing/` | `test_workspace_operator_surface_supports_query_briefing_and_backfill` | `test_restructure_research_architecture.py:234` | `digest_path.exists()`; `# Digest: AI Agents` in digest | ✅ 真实调用 `main()` → `generate_briefing()` → `write_digest_report()` | ✅ 全通过 | ✅ 删 write_digest_report 会红 | ✅ |
| 5 | Partial Progress Continues | Briefing requests a missing source | workspace still writes briefing and marks missing source explicitly | `test_workspace_operator_surface_continues_with_partial_briefing_results` | `test_restructure_research_architecture.py:276` | `"Missing sources: twitter" in digest`; digest_path.exists() | ✅ 真实调用 `main()` → `generate_briefing()` with `requested_sources=["github", "papers", "wechat", "twitter"]` | ✅ 全通过 | ✅ 删 partial-success branch 会红 | ✅ |
| 6 | Runnable Documented Entrypoints | Follow workspace docs | command reaches unified workspace operator surface instead of requiring source-specific wrapper path | `test_workspace_operator_surface_supports_query_briefing_and_backfill` | `test_restructure_research_architecture.py:234` | `main(["query", "agent"]) == 0`; `main(["briefing", "digest", "agent"]) == 0`; backfill sidecar exists | ✅ 真实调用统一 `main()` dispatch | ✅ 全通过 | ✅ 删 main dispatch 会红 | ✅ |
| 7 | Runnable Documented Entrypoints | Backfill historical outputs | backfill command writes sidecars for all parseable historical items while preserving Markdown | `test_workspace_operator_surface_supports_query_briefing_and_backfill` | `test_restructure_research_architecture.py:234` | `github_dir / "research-item.json" exists`; `papers_dir / "01-sample.research-item.json" exists`; `wechat_dir / "research-item.json" exists` | ✅ 真实调用 `main(["backfill", ...])` → `backfill_output_tree()` | ✅ 全通过 | ✅ 删 backfill_output_tree 会红 | ✅ |

## 逐测试函数反模式检查

### `test_restructure_research_architecture.py:138` — `test_library_query_supports_cross_source_and_optional_time_filters`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 6 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 均为具体字段值比较（title sets, source sets） |
| 3 | Happy path only | ✅ 通过 | 同 Requirement 下另有时间过滤边界测试 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `query_research_items()` |
| 5 | 绕开 THEN | ✅ 通过 | assertion 验证 title/source 过滤，与 Spec THEN 一致 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:160` — `test_briefing_reports_generate_obsidian_friendly_markdown`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 10 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 检查 digest_path、文件路径、标题和链接内容 |
| 3 | Happy path only | ✅ 通过 | 同 Requirement 下另有 partial-success 测试 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `write_digest_report()` 和 `write_reading_list_report()` |
| 5 | 绕开 THEN | ✅ 通过 | assertion 验证 `output/briefing/` 路径和 Obsidian 格式 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:182` — `test_briefing_reports_allow_partial_success_with_explicit_source_gap`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 4 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 检查 Missing sources 字符串和 digest 内容 |
| 3 | Happy path only | ✅ 通过 | 覆盖了 missing source 边界场景 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `write_digest_report()` |
| 5 | 绕开 THEN | ✅ 通过 | assertion 明确检查 "Missing sources: wechat" |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:203` — `test_workspace_operator_surface_dispatches_collect_actions`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 8 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 断言调用参数的具体 tuple 值 |
| 3 | Happy path only | ✅ 通过 | 覆盖了 github/papers/wechat 三路 dispatch |
| 4 | Mock 被测函数 | ✅ 通过 | monkeypatch 的是 `collect_github_targets` 等（外部依赖），不是被测函数本身 |
| 5 | 绕开 THEN | ✅ 通过 | assertion 验证 calls == expected tuple，直接对应 Spec THEN |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:234` — `test_workspace_operator_surface_supports_query_briefing_and_backfill`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 9 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 检查文件存在、stdout 内容和 sidecar 路径 |
| 3 | Happy path only | ✅ 通过 | 覆盖了 query / briefing / backfill 三个 business actions |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `main()` dispatch |
| 5 | 绕开 THEN | ✅ 通过 | assertion 验证 query 输出、briefing 路径、sidecar 持久化 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:276` — `test_workspace_operator_surface_continues_with_partial_briefing_results`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 3 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 检查 "Missing sources: twitter" in digest 和 digest_path.exists() |
| 3 | Happy path only | ✅ 通过 | 覆盖了 partial briefing 边界场景 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `main()` dispatch |
| 5 | 绕开 THEN | ✅ 通过 | assertion 明确验证 missing source 标记 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:308` — `test_legacy_entrypoint_runtime_files_are_removed`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 4 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 均为 `assert not path.exists()`，精确验证文件不存在 |
| 3 | Happy path only | ✅ 通过 | 单一清理验证，无边界分支 |
| 4 | Mock 被测函数 | ✅ 通过 | 直接读文件系统 |
| 5 | 绕开 THEN | ✅ 通过 | 与 Spec REMOVED Requirements 完全对应 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

### `test_restructure_research_architecture.py:315` — `test_legacy_source_tool_directories_are_moved_out_of_repo_root`

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 17 个 assert |
| 2 | 断言太弱 | ✅ 通过 | 均为 `assert path.exists()` / `assert not path.exists()`，精确验证 |
| 3 | Happy path only | ✅ 通过 | 覆盖了 4 个来源目录的转移验证 |
| 4 | Mock 被测函数 | ✅ 通过 | 直接读文件系统 |
| 5 | 绕开 THEN | ✅ 通过 | 与 Spec REMOVED Requirements 完全对应 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |

## 覆盖概要

| 能力域 | Requirement | Scenario | ✅ 有效 | 🔴 缺陷 | ❌ 缺失 |
|--------|-------------|----------|---------|---------|---------|
| research-operations | 4 | 6 | 6 (100%) | 0 | 0 |
| system | 1 | 1 | 1 (100%) | 0 | 0 |

## 反模式统计

无命中。

## 覆盖缺口

无。

## 结论

- [x] ✅ 通过 — 主表所有行结论为 ✅，无 🔴 反模式，无 ❌ 缺失

## 循环状态
- 本次已审查: change/add-research-operator-surface
- 本次结论: ✅ 通过
- 队列剩余: 4 项
- 下次调用将审查: separate-legacy-compatibility-layer