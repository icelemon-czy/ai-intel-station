# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 Dashboard 页面命名 - 显示"资料总览"标题和说明
- [x] 1.2 Library 页面命名 - 显示"资料库"标题和说明
- [x] 1.3 Briefing 页面命名 - 显示"生成简报"标题和说明
- [x] 1.4 Collect 页面命名 - 显示"采集资料"标题和说明
- [x] 1.5 页面用途说明 - 显示页面用途说明
- [x] 1.6 下一步 CTA - 显示 CTA 按钮

## 2. Update Navigation Labels

- [x] 2.1 修改 Dashboard 导航标签为"资料总览"
- [x] 2.2 修改 Library 导航标签为"资料库"
- [x] 2.3 修改 Briefing 导航标签为"生成简报"
- [x] 2.4 修改 Collect 导航标签为"采集资料"

## 3. Add Page Purpose Descriptions

- [x] 3.1 为 DashboardSection 添加页面说明
- [x] 3.2 为 LibrarySection 添加页面说明
- [x] 3.3 为 BriefingSection 添加页面说明
- [x] 3.4 为 CollectSection 添加页面说明

## 4. Add Navigation CTAs

- [x] 4.1 在各页面添加指向其他页面的 CTA
- [x] 4.2 确保 CTA 链接正确

## 5. Update Documentation

- [x] 5.1 更新 README 中的 Web 描述
- [x] 5.2 更新 .ai 导航中的页面说明

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->