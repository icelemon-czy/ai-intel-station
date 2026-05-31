# research-web-library-interaction — Delta Spec

> 本文件描述对 `specs/research-web-library-interaction/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: 分页与选中项同步

翻页时如果选中项不在当前页，应清除选中或提示用户。

#### Scenario: 翻页后选中项不可见

- **WHEN** 用户翻页后，之前选中的项不在当前页
- **THEN** 详情面板显示"请在结果列表中选择一项"，并清空 detail 状态

#### Scenario: 重新搜索后清空选中

- **WHEN** 用户修改搜索 keyword 或 sources
- **THEN** 清空当前选中项和详情面板，显示第一页结果