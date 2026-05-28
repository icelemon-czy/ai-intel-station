# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 分页参数传入 API - list_library_items 支持 page 和 page_size 参数
- [x] 1.2 分页元数据返回 - API 返回 total_count, page, page_size, total_pages
- [x] 1.3 翻页状态保持 - 翻页后搜索条件不变
- [x] 1.4 切换每页条数重置 - 修改 page_size 后回到第一页
- [x] 1.5 选中项跨页清除 - 翻页后选中项不在当前页则清空 detail
- [x] 1.6 重新搜索清空选中 - 改变 keyword 或 sources 清空 detail

## 2. Backend API 分页支持

- [x] 2.1 修改 list_library_items 支持 page 和 page_size 查询参数
- [x] 2.2 返回分页元数据（total_count, page, page_size, total_pages）
- [x] 2.3 修改 /api/library GET 端点解析分页参数

## 3. Frontend 分页 UI

- [x] 3.1 添加分页控件（上一页/下一页/页码按钮）
- [x] 3.2 显示 "第 X 页 / 共 Y 页" 和 "当前第 N 条 / 共 M 条"
- [x] 3.3 每页条数选择器（下拉菜单：10/20/50）
- [x] 3.4 管理 page/page_size state

## 4. 分页与选中项同步逻辑

- [x] 4.1 翻页时检查当前选中项是否在当前页
- [x] 4.2 不在时清空 detail 并显示提示
- [x] 4.3 搜索条件变化时清空选中

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->