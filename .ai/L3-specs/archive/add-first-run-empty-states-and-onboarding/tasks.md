# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 Dashboard 空状态 - 无数据时显示"暂无资料，请先采集"文案
- [x] 1.2 Library 空搜索结果 - 无结果时显示引导文案和 CTA
- [x] 1.3 Briefing 空状态 - 无 briefing 产物时显示引导文案
- [x] 1.4 首次访问 onboarding - 首次访问时显示工作流程说明
- [x] 1.5 空状态 CTA 联动 - 提供指向正确操作的 CTA 按钮

## 2. Update Dashboard Empty State

- [x] 2.1 修改 DashboardSection 显示空状态文案
- [x] 2.2 添加"去采集"CTA 按钮
- [x] 2.3 检测本地是否有 research items

## 3. Update Library Empty State

- [x] 3.1 修改 LibrarySection 处理空搜索结果
- [x] 3.2 添加空状态引导文案
- [x] 3.3 添加"去采集更多资料"CTA

## 4. Update Briefing Empty State

- [x] 4.1 修改 BriefingSection 处理无 briefing 产物
- [x] 4.2 添加空状态引导文案
- [x] 4.3 提示用户先检索资料再生成简报

## 5. Add Onboarding Detection

- [x] 5.1 在 App.jsx 中添加首次访问检测
- [x] 5.2 显示 onboarding 提示组件
- [x] 5.3 记住用户已看过 onboarding（sessionStorage）

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->