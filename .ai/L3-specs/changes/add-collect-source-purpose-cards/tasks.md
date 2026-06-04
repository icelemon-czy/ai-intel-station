# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 GitHub source purpose card — backend form metadata lists purpose, required input, output dir, dependency hint
- [x] 1.2 arXiv Papers source purpose card — backend form metadata lists purpose, required input, output dir, dependency hint
- [x] 1.3 WeChat source purpose card — backend form metadata lists purpose, required input, output dir, dependency hint
- [x] 1.4 Purpose card content is rendered in App.jsx — React component reads the new metadata keys

## 2. Backend: extend collect form metadata

- [x] 2.1 在 `COLLECT_SOURCE_FORMS` 中为 `github` / `papers` / `wechat` 增加 `purpose` / `required_input` / `output_dir` / `dependency_hint` 字段
- [x] 2.2 保持现有 `id` / `label` / `description` / `fields` 字段不变以避免破坏现有契约

## 3. Frontend: render purpose card

- [x] 3.1 在 `CollectSection` 表单旁增加 purpose card 容器，按 `formDefinition.purpose` 等字段渲染
- [x] 3.2 切换 active source 时，card 内容随之更新
- [x] 3.3 卡片纯展示，不引入新的 input / button，不影响 Run now 行为

## 4. Wire it up

- [x] 4.1 端到端验证：手动切换 source，cards 渲染符合预期
- [x] 4.2 跑 `tests/test_web_workspace.py` 全绿

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
