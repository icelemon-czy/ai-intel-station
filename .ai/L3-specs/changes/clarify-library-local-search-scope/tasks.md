# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 Backend exposes `library_search_notes()` returning scope + filter + result notes
- [x] 1.2 Library payload includes the scope notes (or App.jsx fetches from a dedicated endpoint)
- [x] 1.3 App.jsx LibrarySection renders the scope / filter / result notes
- [x] 1.4 `list_library_items` behavior is unchanged (no remote call in test that monkeypatches collectors)

## 2. Backend: surface library search scope

- [x] 2.1 在 `workspace_web/service.py` 增加 `library_search_notes()` 返回 scope/filter/result 三段说明
- [x] 2.2 （可选）让 `list_library_items` payload 增加 `search_notes` 字段或暴露 `/api/library/metadata` 端点

## 3. Frontend: render local-search scope copy

- [x] 3.1 LibrarySection 顶部加 scope note（本地归档 / 不触发远程）
- [x] 3.2 Sources/Keyword/Since/Until 附近加 filter-scope 短提示
- [x] 3.3 Results 区域加强 "from output/" 语义
- [x] 3.4 无结果时仍走 Change 2 的 empty-state 面板（不重复实现）

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 端到端验证：手动打开 Library，能看到本地搜索范围说明

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
