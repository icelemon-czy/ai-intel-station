# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 GitHub collect returns unified result - status, message, item_count, saved_paths
- [x] 1.2 Papers collect returns unified result - same structure
- [x] 1.3 WeChat collect returns unified result - same structure

## 2. Backend: 统一结果结构

- [x] 2.1 修改 run_collect 返回 {status, message, item_count, saved_paths}
- [x] 2.2 所有 source 使用相同结构

## 3. Frontend: 展示 item_count 和 saved_paths

- [x] 3.1 CollectSection 显示 item_count 和 saved_paths
- [x] 3.2 统一卡片格式展示结果

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->