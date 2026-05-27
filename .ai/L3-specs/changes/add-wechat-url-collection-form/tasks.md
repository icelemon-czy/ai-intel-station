# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 单 URL 输入 - 显示单 URL 输入框
- [x] 1.2 批量 URL 输入 - 显示多行文本框
- [x] 1.3 URL 合法性校验 - 验证微信 URL 格式
- [x] 1.4 前置条件检查 - 显示 Camoufox 可用性
- [x] 1.5 运行时状态提示 - 显示抓取进度
- [x] 1.6 成功结果摘要 - 显示 Markdown/images/sidecar
- [x] 1.7 失败错误提示 - 显示具体错误原因

## 2. Update WeChat Form in Collect Workspace

- [x] 2.1 在 COLLECT_SOURCE_FORMS 中完善 WeChat 表单定义
- [x] 2.2 支持 URL 和批量 URL 两种模式
- [x] 2.3 添加前置条件状态显示

## 3. Implement URL Validation

- [x] 3.1 实现 validate_wechat_url 函数
- [x] 3.2 验证 URL 格式以 `https://mp.weixin.qq.com/s/` 开头

## 4. Update Collect API

- [x] 4.1 确保 /api/collect/wechat 端点正确处理 URL
- [x] 4.2 集成前置条件检查

## 5. Update Result Display

- [x] 5.1 成功时显示结果摘要
- [x] 5.2 失败时显示错误原因和修复建议

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->