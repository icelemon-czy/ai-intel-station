# research-web-wechat-collection — Delta Spec

> 本文件描述对 `specs/research-web-wechat-collection/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: WeChat URL 输入表单

Web Collect Workspace 应提供 WeChat 专用的 URL 输入表单。

#### Scenario: 单 URL 输入

- **WHEN** 用户选择 WeChat source 并输入单个 URL
- **THEN** 显示 URL 输入框，placeholder 提示 `https://mp.weixin.qq.com/s/...`
- **THEN** 提交前验证 URL 格式为微信文章格式

#### Scenario: 批量 URL 输入

- **WHEN** 用户选择输入多个 URL
- **THEN** 显示多行文本框，每行一个 URL
- **THEN** 系统依次处理每个 URL

#### Scenario: URL 合法性校验

- **WHEN** 用户提交 WeChat URL
- **THEN** 验证 URL 以 `https://mp.weixin.qq.com/s/` 开头
- **THEN** 如果格式不正确，显示"URL 格式不正确，请检查后重新输入"

### Requirement: WeChat 采集前置条件

WeChat 采集需要特定的前置条件，系统应清晰展示。

#### Scenario: 前置条件检查

- **WHEN** 用户打开 WeChat 采集表单
- **THEN** 显示 Camoufox 浏览器可用性状态
- **THEN** 如果不可用，显示"需要安装 Camoufox 浏览器才能采集微信公众号文章"

#### Scenario: 运行时状态提示

- **WHEN** WeChat 采集正在进行
- **THEN** 显示"正在抓取文章，请稍候..."
- **THEN** 显示进度或状态更新

### Requirement: WeChat 采集结果展示

采集完成后应清晰展示结果和落盘信息。

#### Scenario: 成功结果摘要

- **WHEN** WeChat 采集成功完成
- **THEN** 显示"采集成功！"
- **THEN** 显示 Markdown 文件路径、images 数量、sidecar 状态

#### Scenario: 失败错误提示

- **WHEN** WeChat 采集失败
- **THEN** 显示具体错误原因（如"无法访问该文章"、"需要登录验证"）
- **THEN** 提供修复建议