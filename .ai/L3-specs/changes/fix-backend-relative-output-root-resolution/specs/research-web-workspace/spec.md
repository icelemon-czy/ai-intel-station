# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。

## MODIFIED Requirements

### Requirement: serve_workspace Resolves Relative output_root Against Project Root

`workspace_web.server.serve_workspace(output_root)` MUST resolve a relative `output_root` against the project root (the parent directory of the `workspace_web/` package) rather than against the server's current working directory. Absolute paths MUST be passed through unchanged. The resolved absolute path MUST be the one used for all subsequent API requests.

#### Scenario: relative output_root resolved under wrong cwd still finds the data

- **WHEN** the server is started with cwd = `web/` and `output_root = Path('output')`
- **THEN** `serve_workspace` MUST resolve `output_root` to `<project_root>/output`
- **AND** `/api/dashboard` MUST report the actual item count from the project-root `output/` directory
- **AND** the count MUST be > 0 (assuming the directory contains sidecars)

#### Scenario: absolute output_root is passed through

- **WHEN** the server is started with `output_root = Path('/absolute/path/to/output')`
- **THEN** `serve_workspace` MUST use that path verbatim (no project-root anchoring)
- **AND** the path printed to stdout reflects the absolute path

#### Scenario: relative path that does not exist under project root fails fast

- **WHEN** the server is started with `output_root = Path('nonexistent-dir')`
- **THEN** `/api/dashboard` MUST still respond (return empty state) rather than crash
- **AND** the printed "Using output root" line MUST show `<project_root>/nonexistent-dir`
