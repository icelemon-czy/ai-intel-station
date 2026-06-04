# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射。

- [x] 1.1 Null lastError renders no banner markup
- [x] 1.2 Non-null lastError renders the error message
- [x] 1.3 Section change clears the previous error
- [x] 1.4 dismissError callback clears the surfaced error
- [x] 1.5 Hook does not throw when fetcher resolves to null
- [x] 1.6 `npm test --prefix web` runs the full Node + new SSR suite

## 2. Frontend: SSR render test file

- [x] 2.1 创建 `web/test/autoRefresh.react.test.mjs`
- [x] 2.2 用 `react-dom/server` 的 `renderToString` 渲染一个 useAutoRefresh consumer
- [x] 2.3 不引入新依赖

## 3. NPM script wiring

- [x] 3.1 `web/package.json` 加 `"test": "node --test test/*.test.mjs"`
- [x] 3.2 跑 `npm test --prefix web` 确认全绿

## 4. Python: subprocess test

- [x] 4.1 `tests/test_web_workspace.py` 加 1 个 `subprocess.run(["npm", "test", "--prefix", "web"])` 测试

## 5. Wire it up

- [x] 5.1 跑 Node tests (`node --test web/test/`) 全绿
- [x] 5.2 跑 Python tests 全绿
