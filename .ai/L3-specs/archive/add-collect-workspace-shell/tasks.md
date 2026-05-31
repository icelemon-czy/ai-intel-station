# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 采集工作台页面导航 - 用户点击"采集"入口时页面加载采集工作台
- [x] 1.2 Source 切换 - 用户选择不同 source 时表单区域相应变化
- [x] 1.3 采集任务提交 - 用户填写字段并提交后运行状态显示进度
- [x] 1.4 页面说明显示 - 进入采集工作台时显示清晰的页面标题和说明
- [x] 1.5 导航 active 状态 - 点击导航入口时该入口显示 active 样式

## 2. Create Collect Workspace Component

- [x] 2.1 在 App.jsx 中添加 CollectSection 组件框架
- [x] 2.2 在导航中添加 Collect 入口项
- [x] 2.3 实现 source 切换器 UI（WeChat/GitHub/Papers）
- [x] 2.4 实现采集表单区域基础布局
- [x] 2.5 实现运行状态区域
- [x] 2.6 实现结果摘要区域

## 3. Integrate with Navigation

- [x] 3.1 确保导航样式与 Dashboard、Library、Briefing 保持一致
- [x] 3.2 确保 active 状态样式正确应用

## 4. Connect to Backend API

- [x] 4.1 创建 /api/collect 端点处理采集请求
- [x] 4.2 实现 source-specific 表单数据处理
- [x] 4.3 实现任务状态返回机制

## 5. Style Consistency

- [x] 5.1 确保采集工作台面板样式与现有工作区一致
- [x] 5.2 确保响应式布局正常工作

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->