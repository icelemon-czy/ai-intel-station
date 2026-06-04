# Implementation Tasks

## 1. Tests

- [x] 1.1 Scenario 1: relative path resolved under wrong cwd
- [x] 1.2 Scenario 2: absolute path pass-through (subprocess + -u unbuffered + stdout capture)
- [x] 1.3 Scenario 3: nonexistent path fails fast (subprocess + urllib probe + stdout capture)

## 2. Implementation

- [x] 2.1 `serve_workspace` resolves relative `output_root` against project root

## 3. Wire it up

- [x] 3.1 跑 `tests/test_web_workspace.py` 全绿 (95/95)
- [x] 3.2 live `/api/dashboard` 在浏览器显示真实 item count
