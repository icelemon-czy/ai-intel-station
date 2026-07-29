# Compass Context Scaffold and Migration

Use this reference when `.compass/context/` is new, still contains blank templates, or must absorb confirmed facts from an older context directory.

## Contents

- [Installation boundary](#installation-boundary)
- [Expected structure](#expected-structure)
- [Classify existing content](#classify-existing-content)
- [Migrate old context](#migrate-old-context)
- [Minimum useful context](#minimum-useful-context)
- [Scaffold verification](#scaffold-verification)

## Installation boundary

Compass must already be copied into the target project. Treat `.compass/INSTALL.md` as the authority for installation and platform adaptation.

- If `.compass/context/` exists, populate it in place.
- If the whole `.compass/` directory is missing, stop and ask the user to copy `compass/` as `.compass/`.
- If only part of L1-L5 is missing, compare against the copied package before adding anything. Do not invent a parallel template tree.
- Do not create or update platform Skill directories from `build-context`; `.compass/INSTALL.md` and the selected platform installer own that deployment.

## Expected structure

```text
.compass/context/
├── README.md
├── doc-sync.md
├── L1-codebase-map/
│   ├── overview.md
│   ├── architecture.md
│   ├── module-map.md
│   ├── key-files.md
│   ├── features/_feature-template/README.md
│   └── infrastructure/_infrastructure-template/README.md
├── L2-rules/
│   ├── global.md
│   ├── templates.md
│   ├── testing.md
│   └── _module-template.md
├── L3-specs/
│   ├── change-management.md
│   ├── specs/system.md
│   ├── specs/_capability-template/spec.md
│   ├── changes/_change-template/
│   └── archive/
├── L4-session/active-session.md
└── L5-validation/
    ├── validation-rules.md
    ├── traceability/_domain-template.md
    ├── test-specs/_domain-template.md
    └── reports/
```

The package templates are the format authority. Read them before filling a layer; do not copy their examples into project facts.

## Classify existing content

Before writing, classify every relevant file:

| State | Signal | Action |
|:------|:-------|:-------|
| Blank template | Contains placeholders such as `[填写]` and no project facts | Fill only the fields supported by evidence |
| Confirmed project context | Names real modules, files, commands, requirements, or verified evidence | Preserve and update incrementally |
| Stale context | Refers to deleted files, old commands, or contradicted architecture | Correct it and report what became stale |
| Uncertain claim | Cannot be traced to code, config, tests, Git history, or user input | Mark `[待确认：...]` or remove if it has no value |

Never infer that a populated document is correct merely because it is long.

## Migrate old context

When an old `.ai/` directory exists:

1. Inventory both `.ai/` and `.compass/context/`.
2. Map only still-valid project facts into the corresponding L1-L5 layer.
3. Translate paths to `.compass/context/`.
4. Keep the old `.ai/` directory untouched until the user reviews the migration.
5. Report files that could not be mapped safely.

Use this mapping as a starting point, not an automatic copy rule:

| Old content | Current destination |
|:------------|:--------------------|
| Codebase maps, feature notes, architecture | `L1-codebase-map/` |
| Coding conventions, module contracts, testing rules | `L2-rules/` |
| Requirements, changes, decisions tied to a change | `L3-specs/` |
| Resumable working state | `L4-session/active-session.md` |
| Traceability and checked validation evidence | `L5-validation/` |

Do not migrate obsolete platform entrypoints, copied Skills, generated prompts, or claims of successful validation without evidence.

## Minimum useful context

Do not fill every file merely because it exists. Start with:

1. `L1-codebase-map/overview.md` — a small navigation index.
2. `L2-rules/global.md` — confirmed project-wide constraints.
3. `L2-rules/testing.md` — real test commands and conventions.
4. `L3-specs/change-management.md` — only when the project uses the `develop` workflow.

Add detailed feature, infrastructure, Spec, session, and validation files only when they are useful and supported.

## Scaffold verification

```bash
test -d .compass/context/L1-codebase-map
test -d .compass/context/L2-rules
test -d .compass/context/L3-specs
test -d .compass/context/L4-session
test -d .compass/context/L5-validation
test -f .compass/context/L1-codebase-map/features/_feature-template/README.md
test -f .compass/context/L2-rules/_module-template.md
test -f .compass/context/L3-specs/specs/_capability-template/spec.md
test -f .compass/context/L5-validation/validation-rules.md
```

Also confirm there is no second context directory. Report missing or stale platform Skill deployment separately; do not repair it from `build-context`.
