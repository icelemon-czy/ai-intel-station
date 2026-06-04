# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更（针对 `add-frontend-auto-refresh` 的已知缺口）。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Auto-Refresh Exposes Polling Errors

The auto-refresh controller MUST surface polling errors to the caller via an `onError(section, error)` callback, and MUST expose the last error via a `getLastError(section)` accessor. Polling MUST continue despite errors (a failure MUST NOT stop the interval). The UI MUST display the last polling error to the user and MUST provide a way to dismiss it.

#### Scenario: fetcher rejection fires onError

- **WHEN** a polling fetch rejects (network error, HTTP non-2xx, JSON parse error, etc.)
- **THEN** the controller invokes `onError(activeSection, error)` once with the underlying error
- **AND** polling continues — the next interval tick still fires

#### Scenario: getLastError returns the most recent error

- **WHEN** `getLastError(section)` is called after one or more polling failures
- **THEN** it returns the most recent `Error` object for that section
- **AND** it returns `null` if no failure has happened yet, or if the user has dismissed the last error

#### Scenario: successful fetch clears the last error

- **WHEN** a polling fetch resolves successfully after one or more failures
- **THEN** `getLastError(section)` returns `null` again (the connection is healthy)

#### Scenario: User dismisses the error banner

- **WHEN** the operator clicks the dismiss action on the polling error banner
- **THEN** the banner disappears from the UI
- **AND** the next polling failure will re-surface a fresh banner

#### Scenario: Polling error is non-blocking

- **WHEN** an error banner is visible
- **THEN** the operator can still type, search, switch tabs, and run collects
- **AND** the error banner does not block any form / button

#### Scenario: Error message is safe to display

- **WHEN** the error message is shown to the user
- **THEN** it is the underlying `error.message` (or a short derived string)
- **AND** it MUST NOT include stack traces, file paths, or auth tokens
