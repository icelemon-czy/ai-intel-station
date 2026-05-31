# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 GitHub CLI 可用性检查
- [x] 1.2 WeChat 浏览器依赖检查
- [x] 1.3 输出目录写入检查
- [x] 1.4 WeChat URL 合法性检查
- [x] 1.5 GitHub 参数合法性检查
- [x] 1.6 Papers category 合法性检查
- [x] 1.7 诊断页面显示
- [x] 1.8 Dashboard 诊断摘要

## 2. Create Diagnostics Service

- [x] 2.1 创建 diagnostics service
- [x] 2.2 实现 check_github_cli 方法
- [x] 2.3 实现 check_wechat_browser 方法
- [x] 2.4 实现 check_output_writable 方法

## 3. Create Preflight Validation

- [x] 3.1 实现 validate_wechat_url 函数
- [x] 3.2 实现 validate_github_repo 函数
- [x] 3.3 实现 validate_papers_category 函数

## 4. Create Diagnostics API

- [x] 4.1 创建 /api/diagnostics 端点
- [x] 4.2 创建 /api/diagnostics/check/<source> 端点

## 5. Update Collect Form

- [x] 5.1 采集前执行 preflight checks
- [x] 5.2 显示检查结果错误

## 6. Update Dashboard

- [x] 6.1 在 Dashboard 显示依赖状态摘要
- [x] 6.2 提供诊断页面链接

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->