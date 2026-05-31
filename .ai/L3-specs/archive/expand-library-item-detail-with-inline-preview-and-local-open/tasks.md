# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。

- [x] 1.1 Detail panel shows expanded metadata - get_library_item_detail returns more fields
- [x] 1.2 Local open actions exist - detail panel has buttons to open local folder/file

## 2. Backend: 扩展 Detail API

- [x] 2.1 修改 get_library_item_detail 返回更完整的 metadata
- [x] 2.2 添加 item_type、published_at、updated_at 字段

## 3. Frontend: 增强 Detail Panel

- [x] 3.1 显示更多 metadata 字段
- [x] 3.2 添加 "Open local folder" 和 "View Markdown" 按钮
- [x] 3.3 根据 source 类型显示不同的 metadata

## 4. 本地打开动作实现

- [x] 4.1 实现 open_local_folder 函数（使用 Node.js child_process）
- [x] 4.2 在 App.jsx 中添加按钮调用

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->