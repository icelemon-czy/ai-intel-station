# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Collect Source Purpose Cards

Collect Workspace SHALL display a purpose card next to the source-specific form, describing what the active source is good for, what inputs are required, where results are written, and any critical external dependency hint. The card MUST update when the active source changes.

#### Scenario: GitHub source shows purpose card

- **WHEN** the operator selects the `github` source
- **THEN** the form panel renders a purpose card describing GitHub collection
- **AND** the card lists required input (`owner/repo` or search keyword), output directory (`output/github/`), and dependency hint (GitHub CLI access)

#### Scenario: arXiv Papers source shows purpose card

- **WHEN** the operator selects the `papers` source
- **THEN** the form panel renders a purpose card describing arXiv paper collection
- **AND** the card lists required input (arXiv category and max results), output directory (`output/papers/`), and dependency hint (arXiv public API, no auth required)

#### Scenario: WeChat source shows purpose card

- **WHEN** the operator selects the `wechat` source
- **THEN** the form panel renders a purpose card describing WeChat article collection
- **AND** the card lists required input (article URL), output directory (`output/wechat/`), and dependency hint (Camoufox browser runtime)

#### Scenario: Purpose card updates when source switches

- **WHEN** the operator switches the active source
- **THEN** the previously shown purpose card is replaced by the new source's card
- **AND** no stale card content from the previous source remains visible

#### Scenario: Purpose card is purely informational

- **WHEN** the purpose card is displayed
- **THEN** it does not include form input fields, submit buttons, or change collect execution behavior
- **AND** it does not require backend changes to `run_collect()` semantics
