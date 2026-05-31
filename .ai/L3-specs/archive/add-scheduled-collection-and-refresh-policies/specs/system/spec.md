# system — Delta Spec

> 本文件描述对 `specs/system/spec.md` 的增量变更。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: System Boundaries

The system SHALL define clear boundaries for what is and is not supported in the current implementation phase.

#### Scenario: No scheduled background execution

- **WHEN** system is in initial state
- **THEN** scheduled background execution is not supported

#### Scenario: Local-only execution boundary

- **WHEN** the operator interacts with the system
- **THEN** all operations execute locally without requiring remote services or multi-user coordination

### Requirement: Local Scheduled Execution

[新增]

#### Scenario: System supports local scheduled execution

- **WHEN** user configures a schedule for collection
- **THEN** the system supports local scheduled execution as a defined boundary
- **THEN** schedules are stored locally and triggered based on configured frequency

#### Scenario: Schedule triggers job creation

- **WHEN** a scheduled time arrives
- **THEN** a new job is created and added to the job queue
- **THEN** job execution follows the existing job runner model