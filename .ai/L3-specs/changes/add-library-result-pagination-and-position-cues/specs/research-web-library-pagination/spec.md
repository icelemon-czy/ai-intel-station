# research-web-library-pagination — Delta Spec

> 本文件描述对 `specs/research-web-library-pagination/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## ADDED Requirements

### Requirement: Library 结果分页

Library 搜索结果应支持分页浏览，避免一次性渲染全部结果。

#### Scenario: 分页导航

- **WHEN** 用户在 Library 搜索结果页点击页码
- **THEN** 列表显示对应页的结果，每页默认 20 条

#### Scenario: 每页结果数量控制

- **WHEN** 用户选择每页显示的条数
- **THEN** 列表按所选条数分页，总页数随之变化

#### Scenario: 总条数和页数显示

- **WHEN** 用户在 Library 结果区浏览
- **THEN** 显示当前 "第 X 页 / 共 Y 页" 和 "当前第 N 条 / 共 M 条"

### Requirement: 分页状态保持

翻页后应保持搜索条件和筛选状态。

#### Scenario: 翻页后保持搜索条件

- **WHEN** 用户翻到第二页
- **THEN** 搜索 keyword 和 sources 筛选保持不变

#### Scenario: 切换每页条数后重置到第一页

- **WHEN** 用户修改每页条数
- **THEN** 自动回到第一页并重新计算总页数