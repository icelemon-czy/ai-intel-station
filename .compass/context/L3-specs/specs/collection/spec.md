# Collection Specification

## Purpose

定义所有来源共享的 collection contract；来源特有格式分别由 GitHub、Papers 和 WeChat capability Spec 约束。

## Requirements

### Requirement: Supported Sources

collection SHALL 支持 GitHub repository/search、arXiv category 和 WeChat article URL 三类输入。

#### Scenario: Choose a collection source

- **WHEN** operator 从 CLI 或 Web Collect 选择一个受支持来源
- **THEN**系统展示并接受该来源所需输入
- **AND**结果写入对应 source archive

### Requirement: Archive and Sidecar Persistence

成功 collection MUST 同时保留人类可读 Markdown 和对应 ResearchItem sidecar。

#### Scenario: Persist a collected item

- **WHEN**一个来源成功生成 Markdown artifact
- **THEN**artifact 写入 `output/<source>/`
- **AND**同一 source tree 下写入可供 Library 使用的 sidecar

### Requirement: Source-Specific Validation and Errors

collection MUST 在执行前或失败时明确报告无效输入、缺失 dependency 或 remote failure。

#### Scenario: Required dependency is unavailable

- **WHEN** GitHub CLI、WeChat browser runtime 或远端 API 无法完成请求
- **THEN**当前 collect 返回明确错误
- **AND**错误不会被伪装成成功或空结果

### Requirement: Independent Progress

可独立处理的 category 或 source SHOULD 在其他部分失败时继续，并在最终结果中分别报告状态。

#### Scenario: One paper category fails

- **WHEN**一次 papers collection 包含多个 category 且其中一个失败
- **THEN**其他成功 category 仍完成落盘
- **AND**失败 category 被明确报告
