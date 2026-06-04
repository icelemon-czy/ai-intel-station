# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 App.jsx renders briefing flow explanation block (input source + preview/save note)
- [x] 1.2 App.jsx renders digest vs reading-list purpose copy near the Mode selector
- [x] 1.3 App.jsx renders Preview vs Save one-liners next to the action buttons
- [x] 1.4 Briefing service exposes a `mode_purposes` map (or equivalent) so the copy is data-driven

## 2. Backend: surface mode + action explanations

- [x] 2.1 在 `workspace_web/service.py` 增加 `briefing_mode_purposes()` / `briefing_action_purposes()` 常量或函数
- [x] 2.2 暴露 `briefing_flow_notes`（输入来源、preview vs save、产物路径）的字符串供前端读取

## 3. Frontend: render flow explanations

- [x] 3.1 BriefingSection 顶部加 flow 解释 block（输入来源 + preview/save 差异）
- [x] 3.2 Mode 附近加 digest/reading-list 用途 copy
- [x] 3.3 Preview / Save 按钮加一行说明
- [x] 3.4 保存成功展示路径时标识 "derived reading artifact"

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 端到端验证：手动打开 Briefing 页面，3 处说明文案可见

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
