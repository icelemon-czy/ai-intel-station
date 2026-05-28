# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 Collect sources labels match Library source names - list_collect_sources 和 Library 的 source 显示一致
- [x] 1.2 Source 标签在所有页面一致 - 导航和工作区使用相同的 source 标签

## 2. 创建 Source Label 映射

- [x] 2.1 在 service.py 中定义 SOURCE_LABELS 常量
- [x] 2.2 Library 使用 SOURCE_LABELS 显示而非 raw id

## 3. 更新 Library Section

- [x] 3.1 使用 label 映射显示 source 选项
- [x] 3.2 与 Collect workspace 的 source 显示一致

## 4. 回归测试

- [x] 4.1 添加测试验证 source 标签不会漂移

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->