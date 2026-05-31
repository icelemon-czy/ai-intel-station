# research-web-source-taxonomy — Delta Spec

> 本文件描述对 `specs/research-web-source-taxonomy/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: 统一的 Source 标签体系

Web 工作台所有页面必须使用统一的 source 标签，内部 id 与用户可见标签保持一致。

#### Scenario: Library 显示与 Collect 显示一致

- **WHEN** 用户在 Library 筛选 source 和在 Collect 切换 source
- **THEN** 两个页面显示的 source 标签完全一致，都使用 `github` / `papers` / `wechat`

#### Scenario: Source 表单中的标签与 Library 对齐

- **WHEN** 用户在 Collect Workspace 查看 source 切换器
- **THEN** 显示 "GitHub" / "arXiv Papers" / "WeChat Articles" 作为用户可见标签，而非 "arXiv" 或其他别名

### Requirement: Source Label 回归覆盖

新增测试确保 source 标签不会随页面演进再次出现漂移。

#### Scenario: 导航中的 source 选项与工作区显示一致

- **WHEN** 页面渲染 source 标签
- **THEN** 使用统一的 label 定义，不出现同一 source 的多个不同别名