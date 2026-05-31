# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 为 Dashboard 编写测试，覆盖本地归档统计与 recent briefing 概览渲染
- [x] 1.2 为 Dashboard 编写测试，覆盖 missing sidecar / missing source gap 的显式提示
- [x] 1.3 为 Library 编写测试，覆盖关键词、来源和可选时间过滤下的本地结果展示
- [x] 1.4 为 Library 详情视图编写测试，覆盖 sidecar 元数据到详情面板字段的映射
- [x] 1.5 为 Briefing Workspace 编写测试，覆盖 digest / reading-list 预览与保存流程
- [x] 1.6 为 Briefing partial-success 场景编写测试，覆盖 missing sources 提示与保存继续
- [x] 1.7 为系统边界编写测试，覆盖 Web 只读取本地 archive / sidecar 而不触发远程 collect
- [x] 1.8 为 MVP scope guard 编写测试，验证首期导航不暴露 collect / backfill 控制

## 2. Web Runtime Foundation

- [x] 2.1 新建 React Web 工作台与本地启动入口，建立 Dashboard / Library / Briefing Workspace 三个主路由
- [x] 2.2 建立仅面向本地界面的桥接层，让 Web 继续复用现有 archive、query 与 briefing 语义

## 3. Dashboard And Library

- [x] 3.1 实现 Dashboard 的本地归档统计、recent briefing 列表和 coverage / gap 摘要
- [x] 3.2 实现 Library 的查询表单、结果列表和详情视图，复用现有 `ResearchItem` 过滤语义

## 4. Briefing Workspace

- [x] 4.1 实现 Briefing Workspace 的参数配置、预览与保存流程，继续复用本地 query / briefing 规则
- [x] 4.2 保证 partial-success、missing-source 提示和 `output/briefing/` 写入边界在 Web 中保持一致

## 5. Docs And Verification

- [x] 5.1 更新 README、`.ai` 导航和运行说明，补充本地 Web 工作台入口、边界和 MVP 范围
- [x] 5.2 运行新增测试与最小 smoke 验证，确认 Web 层不破坏现有 output / sidecar 契约
