# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。

## MODIFIED Requirements

### Requirement: Library Safe Markdown Preview

The Library page MUST let the operator read the Markdown body of a selected item without leaving the workspace. The backend MUST serve the Markdown via a dedicated API endpoint that is restricted to the current `output_root` and to the `output_path` recorded in the item's sidecar. The UI MUST render a preview region inside the item-detail panel and MUST show a clear error when the file is missing or unreadable.

#### Scenario: preview endpoint returns Markdown for a known sidecar path

- **WHEN** the operator selects a Library item whose `output_path` is `output/github/foo/README.md`
- **AND** the file exists inside the server's `output_root`
- **THEN** the preview API returns the file's text content
- **AND** the response includes a `content_type` of `text/markdown; charset=utf-8`

#### Scenario: preview endpoint rejects paths outside output_root

- **WHEN** the preview API is called with a path that resolves outside the server's `output_root` (e.g. `../etc/passwd`, `/absolute/elsewhere`)
- **THEN** the response is HTTP 400 with an error message
- **AND** the file is NOT read

#### Scenario: preview endpoint rejects paths not present in any sidecar

- **WHEN** the preview API is called with a path that is inside `output_root` but is not the `output_path` of any loaded ResearchItem
- **THEN** the response is HTTP 404 with a "not a known archive entry" message
- **AND** no other file in `output_root` is read

#### Scenario: preview endpoint returns 404 when file is missing

- **WHEN** the path IS a known sidecar `output_path` but the underlying file has been deleted
- **THEN** the response is HTTP 404 with a "file missing" message

#### Scenario: Library detail panel renders a preview region

- **WHEN** the operator has a Library item selected and the preview API returned content
- **THEN** the detail panel shows a `<MarkdownPreview>` element containing the file body
- **AND** the operator does not need to leave the Library page to read the file

#### Scenario: Library detail panel shows a clear error for unreadable Markdown

- **WHEN** the operator has a Library item selected and the preview API returned an error (404 or 400)
- **THEN** the detail panel shows a readable error message
- **AND** does NOT show a broken / blank preview area

#### Scenario: preview does not modify state

- **WHEN** the operator triggers a preview fetch
- **THEN** no files on disk are modified
- **AND** no collect / save / briefing operations are triggered
- **AND** the page state (form, selection, sources) is not altered
