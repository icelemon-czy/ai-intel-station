# research-web-library-interaction — Delta Spec

> 本文件描述对 `specs/research-web-library-interaction/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Library 列表项选中状态

Library 结果列表项应提供明确的选中状态反馈，让用户清楚知道当前选中的是哪一项。

#### Scenario: 结果项点击后显示选中状态

- **WHEN** 用户点击 Library 结果列表中的某个项
- **THEN** 该项显示明确的选中样式（如深色背景），其他项保持默认样式
- **THEN** 右侧详情面板同步更新显示选中项的详细信息

#### Scenario: 结果项 hover 状态

- **WHEN** 用户鼠标悬停在 Library 结果列表中的某个项
- **THEN** 该项显示 hover 样式（如轻微背景色变化），提示用户该项可点击

#### Scenario: 选中项与详情面板同步

- **WHEN** 用户点击某个结果项
- **THEN** 左侧列表中该项保持选中状态，右侧详情面板显示对应详情
- **THEN** 即使页面刷新或重新搜索，选中状态也有合理的默认值（默认选中第一条或保持上次选择）

### Requirement: 键盘导航支持

Library 结果列表应支持键盘导航，提升可访问性。

#### Scenario: 键盘上下导航

- **WHEN** 用户在 Library 结果列表上按上下箭头键
- **THEN** 当前焦点项高亮显示，上下键移动焦点但不触发选择

#### Scenario: Enter 键选择

- **WHEN** 用户在焦点项上按 Enter 键
- **THEN** 该项被选中，显示选中状态，右侧详情面板更新

### Requirement: 移动端触控反馈

Library 结果列表应支持移动端触控交互。

#### Scenario: 触控选择

- **WHEN** 用户在移动端触摸 Library 结果列表中的某个项
- **THEN** 该项显示选中状态（如同点击），右侧详情面板更新