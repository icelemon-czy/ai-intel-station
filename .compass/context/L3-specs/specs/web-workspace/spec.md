# Local Web Workspace Specification

## Purpose

为同一 local archive 提供 Dashboard、Library、Briefing 和 Collect 四个主要交互 surface，并从 Dashboard 触发 daily discovery。

## Boundary

Web workspace 提供本地单机操作，不提供 remote account、多用户权限、通用 job history、schedule CRUD 或 diagnostics dashboard。

## Requirements

### Requirement: Stable Workspace Navigation

Web workspace SHALL 提供 Dashboard、Library、Briefing 和 Collect 导航，并在 section 切换后保持 operator 已输入的 Library filter state。

#### Scenario: Switch away from Library and return

- **WHEN** operator 编辑 Library filter 后切换 section 再返回
- **THEN**keyword、source、date、page 和 page-size state 保持不变

### Requirement: Dashboard Uses Local Truth

Dashboard SHALL 展示 local archive item count、source coverage、recent briefing 和可操作的 empty-state guidance。

#### Scenario: Open Dashboard with an empty archive

- **WHEN**指定 `output_root` 没有 ResearchItem
- **THEN**Dashboard 显示零状态而不是错误
- **AND**提示 collect 或 backfill 的下一步

### Requirement: Library Search and Inspection

Library SHALL 提供 local-only filter、pagination、selection、item detail 和 safe Markdown preview。

#### Scenario: Inspect a selected item

- **WHEN** operator 从 filter result 选择一个 item
- **THEN**detail 显示其 metadata、source link 和 archive path
- **AND**Markdown preview 只读取该 item sidecar 记录且位于 `output_root` 内的文件

#### Scenario: Reject an unknown preview path

- **WHEN** preview request 指向 `output_root` 外或不属于已知 sidecar 的 path
- **THEN**server 拒绝读取并返回明确错误

### Requirement: Explicit Local File Actions

Library MUST NOT 依赖浏览器不安全的 `file://` navigation；它 SHALL 提供 Web preview、source link 和 copy archive path。

#### Scenario: Operator needs the local file

- **WHEN** operator 查看 item detail
- **THEN**UI 提供 copy archive path
- **AND**解释如何在 OS file manager 中使用该 path

### Requirement: Briefing Preview and Save

Briefing workspace SHALL 解释 input source、mode 与 preview/save 差异，并允许 preview 或保存派生 Markdown。

#### Scenario: Preview then save

- **WHEN** operator preview 一个 briefing
- **THEN**content 在页面内显示且尚未写文件
- **AND**operator 明确执行 save 后才写入 `output/briefing/`

### Requirement: Manual Source Collection

Collect workspace SHALL 为 GitHub、Papers 和 WeChat 提供 source-specific form、dependency hint、purpose information 与明确 result summary。

#### Scenario: Complete a manual collect

- **WHEN** operator 选择来源、填写有效输入并执行 Run now
- **THEN**UI 显示 success/error summary、technical details 和 next step
- **AND**成功结果可以进入 Library

### Requirement: Non-Blocking Auto Refresh

active section MAY 每五秒 refresh read data；operator SHALL 能关闭 refresh，失败 MUST 可见且不得清空 form state。

#### Scenario: Polling request fails

- **WHEN** active section 的 refresh request 失败
- **THEN**UI 显示可 dismiss error
- **AND**operator 仍可输入、切换 section 或执行 action

### Requirement: Daily Discovery Action

Dashboard SHALL 提供 daily discovery 的当前状态和手动触发 action。

#### Scenario: Trigger daily discovery from Dashboard

- **WHEN** operator 点击 Run daily discovery now
- **THEN**Web API 启动一个 discovery run 并返回 job identifier
- **AND**Dashboard 可以轮询该 run 直到终态
