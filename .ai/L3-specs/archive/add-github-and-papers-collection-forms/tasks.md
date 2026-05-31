# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 GitHub repo 模式表单 - 用户选择 repo 模式时显示 owner/repo 输入框
- [x] 1.2 GitHub search 模式表单 - 用户选择 search 模式时显示关键词和 max 输入框
- [x] 1.3 GitHub 表单校验 - 格式错误时显示错误提示，不提交请求
- [x] 1.4 Papers category 表单 - 显示 category 和 max 输入框
- [x] 1.5 Papers 多 category 支持 - 支持逗号分隔多个 category
- [x] 1.6 Papers 表单校验 - category 为空时显示错误提示
- [x] 1.7 采集成功/失败反馈 - 显示相应状态信息

## 2. Update Collect Source Forms

- [x] 2.1 扩展 GitHub 表单支持 repo 和 search 两种模式
- [x] 2.2 添加 Papers 表单支持 category 和 max
- [x] 2.3 更新 service.py 中的 COLLECT_SOURCE_FORMS

## 3. Implement Form Validation

- [x] 3.1 实现 GitHub owner/repo 格式校验
- [x] 3.2 实现 GitHub search 关键词必填校验
- [x] 3.3 实现 Papers category 必填校验
- [x] 3.4 实现 max 为正整数校验

## 4. Implement API Endpoints

- [x] 4.1 创建 /api/collect/github 端点
- [x] 4.2 创建 /api/collect/papers 端点
- [x] 4.3 实现 source-specific 参数处理

## 5. UI Updates

- [x] 5.1 更新 CollectSection 组件显示 source-specific 表单
- [x] 5.2 实现 mode 切换器（repo/search for GitHub）
- [x] 5.3 添加错误提示组件
- [x] 5.4 添加成功/失败反馈组件

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->