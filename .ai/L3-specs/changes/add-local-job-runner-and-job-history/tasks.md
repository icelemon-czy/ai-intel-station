# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 任务创建 - 提交任务时创建任务记录
- [x] 1.2 任务状态流转 - 任务状态正确流转
- [x] 1.3 任务历史列表 - 显示所有任务列表
- [x] 1.4 任务状态过滤 - 按状态过滤任务
- [x] 1.5 任务重试 - 失败任务可重试
- [x] 1.6 Dashboard 任务摘要 - Dashboard 显示任务摘要

## 2. Create Job Model and Storage

- [x] 2.1 创建 job model 定义任务结构
- [x] 2.2 创建 job storage 持久化任务
- [x] 2.3 实现任务状态流转逻辑

## 3. Create Job Service

- [x] 3.1 实现 create_job 创建新任务
- [x] 3.2 实现 get_job 获取任务详情
- [x] 3.3 实现 list_jobs 列出任务
- [x] 3.4 实现 update_job_status 更新状态
- [x] 3.5 实现 retry_job 重试任务

## 4. Create Job History API

- [x] 4.1 创建 /api/jobs 端点
- [x] 4.2 创建 /api/jobs/<id> 端点
- [x] 4.3 创建 /api/jobs/<id>/retry 端点

## 5. Integrate with Collect Workspace

- [x] 5.1 采集表单提交时创建 Job
- [x] 5.2 显示 Job 提交状态
- [x] 5.3 实时更新 Job 状态

## 6. Add Dashboard Job Summary

- [x] 6.1 在 Dashboard 显示最近任务
- [x] 6.2 失败任务红色标识
- [x] 6.3 成功任务绿色标识

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->