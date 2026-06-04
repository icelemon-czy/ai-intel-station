# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射。

- [x] 1.1 user-typed keyword survives switch (Python source-level assertion)
- [x] 1.2 user-selected sources survive switch
- [x] 1.3 page index survives switch
- [x] 1.4 state lives in App, not in section component
- [x] 1.5 other sections' form state is unaffected

## 2. Refactor App.jsx — lift Library state

- [x] 2.1 App 顶层 `useState` for `libraryForm` (keyword/sources/since/until) + `libraryPage` + `libraryPageSize`
- [x] 2.2 LibrarySection 接收这些作为 props（不自己 useState）
- [x] 2.3 同时把 Library 的 detail/emptyState/searchNotes/results 保留在 Library（这些是 polling 产生的数据，不属于 form）

## 3. Wire it up

- [x] 3.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 3.2 跑 `web/test/*.test.mjs` 全绿
- [x] 3.3 端到端：在浏览器输入 Library keyword，切到 Dashboard，切回 Library，keyword 仍在
