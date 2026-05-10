# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [ ] 1.1 [Scenario → 测试用例描述]
- [ ] 1.2 [Scenario → 测试用例描述]

## 2. [实现任务组名称]

- [ ] 2.1 [具体任务描述]
- [ ] 2.2 [具体任务描述]

## 3. [实现任务组名称]

- [ ] 3.1 [具体任务描述]
- [ ] 3.2 [具体任务描述]

<!-- 
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
