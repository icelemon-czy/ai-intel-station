# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 GitHub success result includes `summary`, `next_step`, `details` (item_count + saved_paths)
- [x] 1.2 arXiv success result includes `summary`, `next_step`, `details`
- [x] 1.3 WeChat success result includes `summary`, `next_step`, `details`
- [x] 1.4 WeChat missing URL result includes error `summary` + `next_step`
- [x] 1.5 Unknown source error result includes `summary` + `next_step`
- [x] 1.6 App.jsx renders `summary` and `next_step` in CollectSection and demotes JSON to a details block

## 2. Backend: standardize `run_collect` result

- [x] 2.1 在 `run_collect` 中为每个分支补齐 `summary` / `next_step` / `details` 字段
- [x] 2.2 保持现有 `status` / `message` / `item_count` / `saved_paths` 字段不变（向后兼容）
- [x] 2.3 增加一个 helper（如 `_format_collect_result(source, status, ...)`）以保持格式一致

## 3. Frontend: render summary + details

- [x] 3.1 CollectSection 优先显示 `result.summary` 和 `result.next_step`
- [x] 3.2 将原 `result.result` JSON 渲染放到 `<details>`/折叠区或次要区域
- [x] 3.3 成功后继续展示 "Go to Library" CTA

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 端到端验证：手动触发一次 GitHub / WeChat 收集，结果区展示 summary + next_step

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
