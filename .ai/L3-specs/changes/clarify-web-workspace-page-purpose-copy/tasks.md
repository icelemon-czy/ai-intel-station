# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 Backend exposes `page_purpose_cards()` returning 4 entries (dashboard / library / briefing / collect)
- [x] 1.2 Each card has non-empty title / purpose / reads / produces fields
- [x] 1.3 `/api/navigation` payload now includes page-purpose metadata
- [x] 1.4 App.jsx renders purpose card component for each of the 4 sections

## 2. Backend: surface page-purpose metadata

- [x] 2.1 在 `workspace_web/service.py` 增加 `page_purpose_cards()` 返回 4 个 page 的 {id, title, purpose, reads, produces}
- [x] 2.2 让 `workspace_sections()` 的每项增加 `purpose / reads / produces` 字段
- [x] 2.3 不破坏现有 `id` / `label` / `description` 字段

## 3. Frontend: render consistent purpose card

- [x] 3.1 提取一个 `<PagePurposeCard>` 组件（或可复用 block）
- [x] 3.2 在 DashboardSection / LibrarySection / BriefingSection / CollectSection 顶部各渲染一张 purpose card
- [x] 3.3 复用现有 purpose-card 样式类，保证视觉一致

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 端到端验证：4 个页面顶部都有一致的 purpose card

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
