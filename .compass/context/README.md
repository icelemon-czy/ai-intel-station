# Compass Project Context

This directory becomes a project's `.compass/context/` when `compass/` is copied into that project. Populate it in place using only current source code, configuration, tests, or confirmed requirements.

## Minimum set

| File | Requirement | Purpose |
|:-----|:------------|:--------|
| `L1-codebase-map/overview.md` | Required | Small feature and navigation index |
| `L2-rules/global.md` | Required | Confirmed project-wide constraints |
| `L2-rules/testing.md` | Required | Real test commands and conventions |
| `L3-specs/change-management.md` | Required only when using the `develop` workflow | Change states and transition rules |

## Optional layers

- Add detailed L1 feature, architecture, infrastructure, and dependency documents only when they improve navigation.
- Add L2 module rules only for confirmed module-specific contracts.
- Add L3 system/capability specs and active changes only when the project uses spec-driven changes.
- Use L4 session state only when work must resume across sessions.
- Add L5 traceability, test specs, and reports only for evidence that has actually been checked.

Do not treat an empty field or example as project knowledge or a verification result. Keep optional files empty until they become useful; do not create a second context directory.
