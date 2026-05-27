# research-web-onboarding — Delta Spec

> 本文件描述对 `specs/research-web-onboarding/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 空状态引导

Web 工作区应在无数据时显示清晰的引导文案，告知用户下一步应做什么。

#### Scenario: Dashboard 空状态

- **WHEN** 用户访问 Dashboard 但本地没有任何 research items
- **THEN** 显示"暂无资料，请先采集"文案，并提供指向采集入口的引导链接

#### Scenario: Library 空状态

- **WHEN** 用户访问 Library 但搜索结果为空
- **THEN** 显示"没有找到匹配的 research items"文案，并提示可调整搜索条件或先采集资料

#### Scenario: Briefing 空状态

- **WHEN** 用户访问 Briefing Workspace 但没有任何 briefing 产物
- **THEN** 显示"暂无 briefing，请先在 Library 中检索资料再生成简报"文案

### Requirement: 首次使用引导

系统应在用户首次访问时显示 onboarding 提示，说明基本工作流程。

#### Scenario: 首次访问 Dashboard

- **WHEN** 用户首次访问 Web Workspace（本地 archive 为空）
- **THEN** 显示 onboarding 提示，说明"采集 → 检索 → 生成简报"的基本流程

#### Scenario: Onboarding 提示内容

- **WHEN** Onboarding 提示显示
- **THEN** 提示用户系统支持三类来源（GitHub、Papers、WeChat）的资料采集，并说明采集入口位置

### Requirement: 空状态与 CTA 联动

空状态文案应与实际可执行的操作联动，引导用户到正确的工作区。

#### Scenario: Dashboard 空状态 CTA

- **WHEN** Dashboard 显示空状态
- **THEN** 提供"去采集"按钮，点击后导航到 Collect Workspace（如可用）或显示采集功能开发中提示

#### Scenario: Library 空状态 CTA

- **WHEN** Library 显示空搜索结果
- **THEN** 提供"去采集更多资料"链接，引导用户进行采集操作