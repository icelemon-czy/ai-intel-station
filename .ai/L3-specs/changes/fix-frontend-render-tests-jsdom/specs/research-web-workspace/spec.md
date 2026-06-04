# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更（针对 `add-frontend-auto-refresh` 的 known gap）。
> 归档时 Agent 会将这些变更合并到主 spec 中。

## MODIFIED Requirements

### Requirement: Auto-Refresh Hook Renders Last Error in DOM

The `useAutoRefresh` React hook MUST expose its `lastError` state to callers such that when the caller renders the returned value into a DOM node, the error message text is visible to the user. When `lastError` is `null`, no error markup MUST be rendered.

#### Scenario: null lastError renders no error markup

- **WHEN** the hook has no recorded error (`lastError === null`)
- **AND** the caller renders `{lastError ? <ErrorBanner error={lastError} /> : null}` via `renderToString`
- **THEN** the resulting HTML MUST NOT contain any error-banner element

#### Scenario: non-null lastError renders the error message

- **WHEN** the hook records an error whose `message` is a known string
- **AND** the caller renders an error banner that displays `error.message`
- **THEN** the rendered HTML MUST contain the message text

#### Scenario: section change clears the previous error

- **WHEN** the hook's `section` prop changes
- **THEN** the surfaced `lastError` MUST reset to `null` on the next render

#### Scenario: dismissError callback clears the surfaced error

- **WHEN** the caller invokes the returned `dismissError()` function
- **THEN** on the next render `lastError` MUST be `null`

#### Scenario: hook does not throw when fetch data is null

- **WHEN** the controller's fetcher resolves to `null` (e.g. test stub) and the hook's `onData` is a no-op
- **THEN** `renderToString` of the consumer MUST NOT throw

#### Scenario: test suite is wired to `npm test --prefix web`

- **WHEN** a CI step runs `npm test --prefix web`
- **THEN** the existing Node tests PLUS the new SSR render tests MUST all run via `node --test` and report pass/fail counts
