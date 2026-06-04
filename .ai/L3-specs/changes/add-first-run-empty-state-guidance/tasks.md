# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 Dashboard empty-state — when `total_items == 0`, `build_dashboard_overview` reports a `empty_state` payload with explanation and next-step pointers
- [x] 1.2 Library empty-state — when `list_library_items` returns zero items, payload exposes `empty_state` block
- [x] 1.3 Briefing empty-state — when preview has no content, payload exposes `empty_state` block pointing to local library
- [x] 1.4 Collect empty-state — App.jsx renders an empty-state panel before first run

## 2. Backend: surface empty-state metadata

- [x] 2.1 在 `build_dashboard_overview` 中当 `total_items == 0` 时增加 `empty_state: {explanation, next_steps}` 字段
- [x] 2.2 在 `list_library_items` 中当结果为空时增加 `empty_state` 字段
- [x] 2.3 在 `preview_briefing` 中当 `item_count == 0` 时增加 `empty_state` 字段
- [x] 2.4 不破坏现有字段，新增字段都是可选的（key 不存在时不应报错）

## 3. Frontend: render empty-state panels

- [x] 3.1 DashboardSection：当 `overview.empty_state` 存在时渲染空状态 panel
- [x] 3.2 LibrarySection：当 `items.empty_state` 存在时渲染空状态 panel
- [x] 3.3 BriefingSection：当 `preview` 为空且 `form.empty_state` 存在时渲染空状态 panel
- [x] 3.4 CollectSection：默认渲染起步提示 panel（不阻塞 form）

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 端到端验证：清空 `output/`，访问每个页面都能看到空状态说明

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
