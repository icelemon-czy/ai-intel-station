# Fix: Backend Resolves Relative output_root Against Project Root

> **状态**: approved
> **创建**: 2026-06-03
> **父变更** (parent-change): 无（无对应原变更；新发现的已 approved 功能 bug）
> **嵌套深度** (depth): 0

## Why

用户报告：磁盘 `output/` 下有 16 个 `research-item.json` sidecar 和 21 个 markdown 文件，但前端 Dashboard 显示 0 items、Library 列表为空。

**根因**：`workspace_web.server.serve_workspace(output_root: Path)` 接收相对路径时**用调用方 cwd 解析**。当前 backend 进程用 `python3 -c "... serve_workspace(Path('output'))"` 启动，cwd 是 `web/`（vite 工作目录），所以 `Path('output')` 解析为 `web/output`（不存在）— backend 静默返回 0 items。

## What Changes

- `serve_workspace` 把相对 `output_root` 解析为相对**项目根**（`workspace_web/` 父目录）的绝对路径
- 绝对路径 pass-through 不变
- 新增 `test_serve_workspace_resolves_relative_output_root_against_project_root` 用 subprocess + 错误 cwd 验证修复
- 不改变 API contract，不改变 serve_workspace 签名

## Alternatives Considered

1. **改调用方** — 改成绝对路径。但当前 backend 是 shell 一次性 `python3 -c`，绝对路径易踩坑
2. **改 server.py 启动时 chdir 到项目根** — 可行但有副作用（破坏 pytest collection 等）
3. **改 serve_workspace 解析路径（当前选择）** — 行为只在 server 内部，不影响其他调用方

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: `serve_workspace` 必须在不同 cwd 下都能正确解析 output_root

## Impact

- `workspace_web/server.py`：单行 resolve 改动
- `tests/test_web_workspace.py`：新增 1 个 subprocess 测试
- 不涉及业务代码 / 后端其他逻辑

## Review Feedback

- [x] 2026-06-03 /review-tests: Scenario 2 (absolute path pass-through) 无测试覆盖 → /fix-bug Step 3B 补测试
- [x] 2026-06-03 /review-tests: Scenario 3 (nonexistent relative path fails fast) 无测试覆盖 → /fix-bug Step 3B 补测试

## Known Gaps

- [ ] 不验证 serve_workspace 被 `python -m workspace_web` 启动时（边缘）
- [ ] 不验证绝对路径行为（但 Path.resolve 是标准行为，信任）
