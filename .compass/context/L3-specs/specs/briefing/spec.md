# Briefing Specification

## Purpose

从 local Library 生成适合 Obsidian 阅读的 digest 或 reading list，不重新抓取远端来源。

## Requirements

### Requirement: Local Briefing Input

briefing SHALL 只消费本地 ResearchItem query result。

#### Scenario: Generate from local archive

- **WHEN** operator 生成 briefing
- **THEN**输入来自指定 `output_root` 的 sidecar
- **AND**不会触发 GitHub、arXiv 或 WeChat fetch

### Requirement: Digest and Reading List Modes

briefing SHALL 支持 digest 和 reading-list 两种派生阅读 artifact。

#### Scenario: Select a mode

- **WHEN** operator 选择 digest 或 reading-list
- **THEN**系统生成对应结构的 Markdown
- **AND**保留 item source link 与必要 metadata

### Requirement: Derived Output Boundary

保存的 briefing MUST 写入 `output/briefing/`，不得覆盖 source archive。

#### Scenario: Save briefing

- **WHEN** briefing save 成功
- **THEN**文件写入 digest 或 reading-list 的派生目录
- **AND**`output/github|papers|wechat` 中的 raw artifact 不被修改

### Requirement: Explicit Source Gaps

缺失请求来源或无匹配 item 时，briefing MAY 继续生成，但 MUST 解释 coverage gap。

#### Scenario: Requested source has no items

- **WHEN**其他来源有结果但某个请求来源为空
- **THEN**生成的 briefing 保留成功内容
- **AND**明确标记缺失来源

### Requirement: Preview and Listing

operator SHALL 能在写文件前 preview briefing，并能只读列出已有 briefing。

#### Scenario: Preview without saving

- **WHEN** operator 请求 preview
- **THEN**系统返回派生 Markdown content
- **AND**不会创建 briefing file
