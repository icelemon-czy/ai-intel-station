# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 最近任务列表 - 显示最近 5 个任务状态
- [x] 1.2 任务状态颜色标识 - 成功绿色/失败红色/进行中黄色
- [x] 1.3 数据时间戳显示 - 显示最后采集时间
- [x] 1.4 数据缺失提示 - 缺少 source 时显示提示
- [x] 1.5 行动入口卡片 - 显示"去采集"等卡片
- [x] 1.6 推荐动作 - 根据状态显示推荐动作
- [x] 1.7 依赖状态摘要 - 显示依赖可用性

## 2. Update Dashboard Overview

- [x] 2.1 扩展 build_dashboard_overview 返回任务摘要
- [x] 2.2 添加数据 freshness 信息
- [x] 2.3 添加行动入口数据

## 3. Update DashboardSection UI

- [x] 3.1 显示最近任务列表
- [x] 3.2 显示任务状态颜色标识
- [x] 3.3 显示数据时间戳和 freshness
- [x] 3.4 显示行动入口卡片

## 4. Add Action Cards

- [x] 4.1 添加"去采集资料"卡片
- [x] 4.2 添加"去资料库搜索"卡片
- [x] 4.3 添加"生成简报"卡片

## 5. Add Dependency Status

- [x] 5.1 在 Dashboard 显示依赖状态
- [x] 5.2 不可用时显示修复建议

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->