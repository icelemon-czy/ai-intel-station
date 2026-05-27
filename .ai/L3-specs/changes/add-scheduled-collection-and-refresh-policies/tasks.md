# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 创建 Schedule - 创建新的定时任务配置
- [x] 1.2 Schedule 频率选项 - 支持每天/每周/每月/cron
- [x] 1.3 Schedule 启停控制 - 启用/停用状态切换
- [x] 1.4 Schedule 与 Jobs 联动 - schedule 触发创建 Job
- [x] 1.5 Schedule 列表视图 - 显示所有 schedule 列表
- [x] 1.6 Schedule 状态指示 - 启用/停用状态显示
- [x] 1.7 Refresh Policy 配置 - 配置刷新频率和保留时间

## 2. Create Schedule Model

- [x] 2.1 创建 schedule model 定义
- [x] 2.2 实现 schedule storage
- [x] 2.3 实现 schedule 频率计算

## 3. Create Schedule Service

- [x] 3.1 实现 create_schedule
- [x] 3.2 实现 get_schedule
- [x] 3.3 实现 list_schedules
- [x] 3.4 实现 update_schedule
- [x] 3.5 实现 delete_schedule

## 4. Integrate with Job Runner

- [x] 4.1 schedule 到期触发 job 创建
- [x] 4.2 job 执行后更新 schedule 下次执行时间

## 5. Create Schedule UI

- [x] 5.1 schedule 管理页面
- [x] 5.2 创建/编辑 schedule 表单
- [x] 5.3 schedule 列表和状态显示

## 6. Update System Spec

- [x] 6.1 修改 system spec 支持本地定时执行
- [x] 6.2 明确 schedule 的系统边界

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->