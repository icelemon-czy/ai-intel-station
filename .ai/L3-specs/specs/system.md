# System Specification (TOR — Top-Level Requirements)

> 系统级顶层需求。定义系统边界、核心约束、跨域需求。
> 新项目可以为空，随变更逐步积累。

## System Boundary

This workspace SHALL provide local-first research tooling that ingests AI-related content from supported external sources and saves Markdown artifacts under `output/`.

Included in boundary:

- WeChat article ingestion
- GitHub repository and search snapshot generation
- arXiv paper ingestion by category
- `.ai/` context, rules, specs, and validation artifacts that describe the above behavior

Excluded from boundary:

- Remote API serving
- Scheduled background execution
- Twitter ingestion, until the workspace gains a real `collect/` implementation and unified `research` entrypoint support

## Cross-Cutting Requirements

### Requirement: Source-Segregated Archive

All generated artifacts SHALL be written to source-specific subdirectories under `output/`.

#### Scenario: Generate a WeChat article

- **WHEN** the WeChat ingestion command succeeds
- **THEN** it writes files only under `output/wechat/`

#### Scenario: Generate GitHub or arXiv artifacts

- **WHEN** a GitHub or papers command succeeds
- **THEN** it writes files only under `output/github/` or `output/papers/`

### Requirement: Traceable Markdown Artifacts

Every generated Markdown artifact SHALL preserve enough metadata to identify the original source.

#### Scenario: Save a repository snapshot

- **WHEN** a repo snapshot is written
- **THEN** the Markdown includes the repository URL and summary metadata

#### Scenario: Save a paper summary

- **WHEN** a paper summary is written
- **THEN** the Markdown includes the arXiv abstract URL or PDF URL and publication metadata

### Requirement: Runnable Documented Entrypoints

Each supported capability SHALL have at least one documented command that can be executed from the workspace using the documented runtime rules.

#### Scenario: Follow workspace docs

- **WHEN** an operator follows the command documented in `.ai` or workspace README files
- **THEN** the command reaches the unified workspace operator surface instead of requiring a source-specific wrapper path

### Requirement: Explicit External Dependency Failure

Failures caused by authentication, browser runtime, or remote API access SHALL be surfaced explicitly to the operator.

#### Scenario: GitHub CLI unavailable

- **WHEN** `gh` returns a non-zero result
- **THEN** the GitHub command fails with explicit stderr context

#### Scenario: arXiv category fetch fails

- **WHEN** a papers category request raises an exception
- **THEN** the tool reports the failing category instead of silently skipping it

### Requirement: Optional Live Verification

Network- or browser-dependent live verification SHOULD remain opt-in and SHALL skip cleanly when prerequisites are absent.

#### Scenario: WeChat live test without URLs

- **WHEN** `WECHAT_E2E_URLS` is unset
- **THEN** the live e2e test is skipped rather than treated as a product failure
