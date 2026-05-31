# collect — Delta Spec

> 本文件描述对 `specs/collect/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: WeChat Collect API

[新增]

#### Scenario: Collect WeChat article via URL

- **WHEN** operator runs `research collect wechat <url>`
- **THEN** the system validates URL format as WeChat article URL
- **THEN** the system uses Camoufox to fetch the article content
- **THEN** the system writes markdown, images, and sidecar to output/wechat/<hash>/

#### Scenario: WeChat URL validation

- **WHEN** URL is submitted for WeChat collection
- **THEN** the system validates URL starts with `https://mp.weixin.qq.com/s/`
- **THEN** if invalid, returns error without attempting collection

### Requirement: Web WeChat Collect Integration

[新增]

#### Scenario: Web submits WeChat collect request

- **WHEN** user submits WeChat URL from Web Collect Workspace
- **THEN** the request routes through unified collect surface with wechat source
- **THEN** preflight checks verify browser availability before attempting collect