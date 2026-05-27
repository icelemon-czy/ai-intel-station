# research-web-runtime-diagnostics — Delta Spec

> 本文件描述对 `specs/research-web-runtime-diagnostics/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 依赖可用性检查

系统在执行采集前应检查各 source 的依赖是否可用。

#### Scenario: GitHub CLI 可用性检查

- **WHEN** 系统需要执行 GitHub 采集
- **THEN** 检查 `gh` CLI 是否已安装且已认证
- **THEN** 如果不可用，显示具体的错误信息和修复建议

#### Scenario: WeChat 浏览器依赖检查

- **WHEN** 系统需要执行 WeChat 采集
- **THEN** 检查 Camoufox 浏览器是否可用
- **THEN** 如果不可用，显示错误信息说明需要安装或配置

#### Scenario: 输出目录写入检查

- **WHEN** 系统需要执行任何采集
- **THEN** 检查 output 目录是否可写
- **THEN** 如果不可写，显示需要创建目录或修改权限的提示

### Requirement: Source-specific Preflight Checks

每个 source 在采集前应进行特定的参数校验。

#### Scenario: WeChat URL 合法性检查

- **WHEN** 用户提交 WeChat URL 进行采集
- **THEN** 验证 URL 格式为 `https://mp.weixin.qq.com/s/...`
- **THEN** 如果格式不合法，显示"URL 格式不正确，请检查后重新输入"

#### Scenario: GitHub 参数合法性检查

- **WHEN** 用户提交 GitHub repo 模式采集
- **THEN** 验证 owner/repo 格式合法
- **THEN** 如果格式不合法，显示"请输入正确的 owner/repo 格式"

#### Scenario: Papers Category 合法性检查

- **WHEN** 用户提交 Papers 采集
- **THEN** 验证 category 为有效的 arXiv category
- **THEN** 如果不合法，显示"无效的 category，请使用如 cs.AI, cs.LG 等格式"

### Requirement: 诊断结果展示

系统应在 Dashboard 或诊断页面展示所有依赖和配置的状态。

#### Scenario: 诊断页面显示

- **WHEN** 用户访问诊断页面
- **THEN** 显示所有 source 的依赖状态（GitHub CLI、WeChat 浏览器、output 目录）
- **THEN** 每项状态显示：可用（绿色）、不可用（红色）、需要配置（黄色）

#### Scenario: Dashboard 显示诊断摘要

- **WHEN** Dashboard 加载时
- **THEN** 显示关键依赖的状态摘要
- **THEN** 如果有不可用的依赖，提供链接到诊断页面