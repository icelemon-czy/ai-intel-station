# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 Collect success provides CTA - run_collect returns result with navigation suggestion
- [x] 1.2 Dashboard updates after collect - total_items reflects new items

## 2. Frontend: Collect 后提供 CTA

- [x] 2.1 CollectSection 在成功结果显示"去 Library 查看"按钮
- [x] 2.2 按钮点击后导航到 Library 并刷新搜索结果

## 3. 刷新机制

- [x] 3.1 导航到 Library 时自动刷新结果
- [x] 3.2 Dashboard 可以通过重新请求 /api/dashboard 获取最新统计

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->