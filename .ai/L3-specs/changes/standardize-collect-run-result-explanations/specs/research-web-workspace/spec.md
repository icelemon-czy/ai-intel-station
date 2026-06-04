# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Standardized Collect Run Result Explanations

`run_collect()` MUST return a normalized result with a human-readable summary AND a structured technical detail block. The summary MUST include the source, outcome status, items collected/written, save path, and recommended next step. The technical detail block MAY contain the raw structured fields (e.g. `item_count`, `saved_paths`) for callers that need them.

#### Scenario: Successful collect result

- **WHEN** a GitHub / arXiv / WeChat collect completes successfully
- **THEN** the result includes `status: "success"`, a one-line `summary` describing the run, `next_step` recommending where to view the items, and a `details` dict with `item_count` and `saved_paths`

#### Scenario: Failed collect result

- **WHEN** a collect fails (invalid input, missing URL, unknown source, etc.)
- **THEN** the result includes `status: "error"`, a `summary` describing the failure in plain language, `next_step` suggesting what to check, and a `details` dict with the raw error context

#### Scenario: Backend result preserves existing field semantics

- **WHEN** the standardized fields are added
- **THEN** the existing `message` / `item_count` / `saved_paths` fields remain present (callers using them MUST not break)

#### Scenario: Frontend renders summary first, details second

- **WHEN** the Collect Workspace shows a run result
- **THEN** the result panel renders `summary` and `next_step` as the primary copy
- **AND** `result.result` (or `details`) is rendered as a collapsible / secondary technical-detail block

#### Scenario: Successful result still offers the Library CTA

- **WHEN** a run completes successfully
- **THEN** the panel still surfaces a CTA to jump to the Library page so the user can review the new items
