# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。

## MODIFIED Requirements

### Requirement: Library Detail Actions Replace file:// with Explicit Local Actions

The Library item-detail panel MUST NOT construct a `file://` URL for the selected item's archive path. The actions panel MUST offer three explicit, well-labelled actions:

1. **Preview Markdown** — fetches the sidecar's Markdown body via `/api/library/preview` and renders it in-page (the `MarkdownPreview` component introduced by `add-library-safe-markdown-preview`).
2. **Open source link** — opens the item's `canonical_url` in a new tab.
3. **Copy archive path** — copies the item's `output_path` to the clipboard and shows a transient "copied" confirmation.

The UI MUST include a small "About local files" note that explains the operator can paste the copied path in their OS file manager (Finder / Explorer) to open the file locally — the workspace deliberately does not invoke a local-folder opener itself.

#### Scenario: detail-actions do NOT contain file:// references

- **WHEN** the Library item-detail panel is rendered
- **THEN** the rendered HTML / source MUST NOT contain a literal `file://` URL for `detail.output_path`
- **AND** MUST NOT contain a `window.open(\`file://...\`)` call

#### Scenario: detail-actions offer Preview Markdown

- **WHEN** the operator views the detail panel
- **THEN** a button or link labelled `Preview Markdown` is present
- **AND** the click handler is bound to the in-page `MarkdownPreview` component (NOT a `window.open`)

#### Scenario: detail-actions offer Open source link

- **WHEN** the operator views the detail panel
- **THEN** an anchor labelled `Open source link` (or equivalent) is present
- **AND** its `href` is `detail.canonical_url`, with `target="_blank"` and `rel="noreferrer"`

#### Scenario: detail-actions offer Copy archive path

- **WHEN** the operator views the detail panel
- **THEN** a button labelled `Copy archive path` is present
- **AND** its click handler invokes the browser clipboard API with `detail.output_path`
- **AND** immediately after a successful copy, the button label (or a sibling status) shows "Copied" for at least 1 second

#### Scenario: clipboard API failure falls back gracefully

- **WHEN** the operator clicks `Copy archive path` but the browser blocks clipboard access (e.g. insecure context)
- **THEN** the action does NOT throw an unhandled error
- **AND** a visible message asks the user to copy the path manually
- **AND** the path is selected / shown read-only in a fallback input (if feasible) — OR a status text displays the path verbatim

#### Scenario: about-local-files note is visible

- **WHEN** the Library page is open
- **THEN** a small "About local files" explanatory note is rendered near the detail panel
- **AND** the note explains that the workspace does not open local files directly and instructs the user to paste the path in their OS file manager

#### Scenario: clipboard call uses navigator.clipboard.writeText

- **WHEN** `Copy archive path` is clicked
- **THEN** the source MUST use the modern `navigator.clipboard.writeText` API
- **AND** MUST NOT rely on the deprecated `document.execCommand('copy')` fallback
