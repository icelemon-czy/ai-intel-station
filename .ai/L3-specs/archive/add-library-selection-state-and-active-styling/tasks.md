# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 结果项点击后显示选中状态
- [x] 1.2 结果项 hover 状态
- [x] 1.3 选中项与详情面板同步
- [x] 1.4 键盘上下导航
- [x] 1.5 Enter 键选择
- [x] 1.6 移动端触控选择

## 2. Update CSS for Active/Hover States

- [x] 2.1 在 styles.css 中添加 result-item active 样式
- [x] 2.2 在 styles.css 中添加 result-item hover 样式
- [x] 2.3 确保 active 样式与默认样式明显区分

## 3. Update LibrarySection Component

- [x] 3.1 在 LibrarySection 中添加 selectedItem state
- [x] 3.2 为 result-item 添加 onClick 处理
- [x] 3.3 为 result-item 添加 className conditional for active state
- [x] 3.4 确保选中项与详情面板同步更新

## 4. Add Keyboard Navigation

- [x] 4.1 在 result-list 上添加 onKeyDown 处理
- [x] 4.2 实现上下箭头键导航
- [x] 4.3 实现 Enter 键选择

## 5. Ensure Touch Support

- [x] 5.1 确保 onClick 在移动端正常工作
- [x] 5.2 测试移动端触控交互

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->