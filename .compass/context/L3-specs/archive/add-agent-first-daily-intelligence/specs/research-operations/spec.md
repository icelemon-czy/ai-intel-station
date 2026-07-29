# Research Operations — Delta Spec

> 本文件描述对 `specs/research-operations/spec.md` 的增量变更。
> 已于 2026-07-25 合并到 main Spec，保留为 archive evidence。

## ADDED Requirements

### Requirement: Lightweight Core Runtime

default project environment SHALL 支持 GitHub、Papers、local query、briefing 与 discovery
control actions，而不安装 WeChat browser stack 或 test-only dependency；source-specific
optional dependency MUST NOT 阻止 core command surface 启动。

#### Scenario: Bootstrap the default operator environment

- **WHEN** fresh environment 只安装 project default dependency
- **THEN**base install 不包含 Camoufox、Playwright、BeautifulSoup、markdownify、httpx 或 pytest
- **AND**`research --help` 与 network-free `research discover --dry-run` 可以启动

#### Scenario: Install an optional source runtime

- **WHEN**operator 明确安装 `wechat` extra
- **THEN**WeChat collection 所需 browser、HTML conversion 与 image download dependency 被安装
- **AND**core command contract 保持不变
