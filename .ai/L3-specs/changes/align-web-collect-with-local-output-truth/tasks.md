# tasks.md — align-web-collect-with-local-output-truth

> 状态: implementing | 创建: 2026-05-27

## Phase B: Delta Spec

- [x] 创建 `specs/research-web-collect-persistence/spec.md`

## Phase C: TDD

- [x] Step 6a: 新增测试 — `test_run_collect_github_writes_to_output_root`
- [x] Step 6b: 新增测试 — `test_run_collect_papers_saves_to_output_root`
- [x] Step 6c: 新增测试 — `test_run_collect_wechat_uses_output_root_and_awaits`
- [x] Step 6d: 更新 `test_run_collect_papers` — 补充 mock `save_papers`
- [x] Step 6e: 更新 `test_run_collect_wechat` — 改为 async mock
- [x] Step 7a: `workspace_web/service.py` — add `output_root` param, fix 3 handlers
- [x] Step 7b: `workspace_web/server.py` — pass `output_root` to `run_collect()`
- [x] Step 7c: run tests → all green (29/29)

## Files Affected

| File | 动作 |
| :--- | :--- |
| `workspace_web/service.py` | MODIFY — `run_collect()` 增加 `output_root`, 修复 3 个 handler |
| `workspace_web/server.py` | MODIFY — POST `/api/collect/run` 透传 `output_root` |
| `tests/test_web_workspace.py` | MODIFY — 新增 3 tests, 更新 2 tests |
