# L1 Codebase Discovery

Use this reference to scan a project, identify infrastructure and product features, and build the lightweight L1 navigation index. Complete it before `l1-deep-analysis.md`.

## Contents

- [Principles](#principles)
- [Phase 1: collect raw signals](#phase-1-collect-raw-signals)
- [Phase 2: identify boundaries](#phase-2-identify-boundaries)
- [Phase 3: fill overview](#phase-3-fill-overview)
- [Phase 4: prepare handoff](#phase-4-prepare-handoff)
- [Quality checks](#quality-checks)

## Principles

- Keep `overview.md` below 60 lines whenever practical. It is an index, not a design document.
- Describe product capabilities as features; do not use source directories as feature names unless the project itself uses those terms.
- Separate shared infrastructure from product features.
- Record facts that save future investigation: entrypoints, data-flow starting points, non-obvious dependencies, operational traps, and required follow-up actions.
- Omit directory listings and facts a later Agent can obtain immediately with `find` or `rg`.
- Use project vocabulary. Mark uncertainty as `[待确认：...]`.

## Phase 1: collect raw signals

Start broad and cheap. Adapt commands to the target project; never assume a language or build system.

```bash
# Shallow structure; exclude generated and dependency directories discovered in the project
find . -maxdepth 3 \
  -not -path '*/.git/*' \
  -not -path '*/node_modules/*' \
  -not -path '*/dist/*' \
  -not -path '*/build/*' \
  -not -path '*/target/*' \
  -not -path '*/__pycache__/*' | sort | head -160

# Common project metadata; read only files that exist
ls package.json pyproject.toml go.mod Cargo.toml pom.xml build.gradle Makefile 2>/dev/null

# Recent change vocabulary and branch conventions
git log --oneline -20 2>/dev/null
git branch -a 2>/dev/null | head -30

# Tests and potential hazards
find . -type f \( -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*' -o -name '*_test.*' \) | head -50
rg -n 'TODO|FIXME|HACK|WARN|DEPRECATED|LEGACY' --glob '!node_modules/**' --glob '!dist/**' --glob '!build/**' . | head -80
```

Then read, rather than merely list:

1. The main README and package/build metadata.
2. Real runtime entrypoints.
3. Lint, formatter, compiler, and test configuration.
4. Representative public API declarations.
5. User-provided architecture, PRD, or terminology documents.

Do not recursively read every file. Use imports, route registration, command wiring, dependency injection, or framework registration to choose representative files.

## Phase 2: identify boundaries

### 2.1 Identify shared infrastructure

Treat a mechanism as infrastructure when it is shared by at least two features or controls project-wide execution. Examples include configuration, dependency injection, persistence infrastructure, message transport, logging, build pipelines, test infrastructure, or plugin hosting.

Keep a helper used by only one feature inside that feature.

Produce:

| Infrastructure component | Representative files | Consumers | One-line responsibility |
|:-------------------------|:---------------------|:----------|:------------------------|
| ... | ... | ... | ... |

If there is no meaningful shared infrastructure, record `none` rather than inventing a layer.

### 2.2 Identify product features

Aim for a small set of business capabilities, usually 3-8:

| Feature | Suspected entrypoint | Trace start | Size | One-line responsibility |
|:--------|:---------------------|:------------|:-----|:------------------------|
| user-auth | `src/auth/routes.ts` | `login()` | medium | Login, registration, and token refresh |

Sizing guidance:

- `small`: logic is concentrated; one feature README may be enough.
- `medium`: two or three meaningful internal layers.
- `large`: several call paths or subsystems requiring layered documents.

Validate each boundary by reading at least one real entrypoint and following enough of its call chain to confirm that the feature exists.

### 2.3 Identify cross-feature signals

Collect:

- Repeated implementation sequences that can become task recipes.
- Generated or legacy areas that must not be edited directly.
- Configuration or schema changes with non-obvious downstream consumers.
- Project-specific terms an Agent is likely to misunderstand.
- Runtime flows that will require deeper analysis.

## Phase 3: fill overview

Read `.compass/context/L1-codebase-map/overview.md` before editing it. Fill only supported fields:

- Project identity and actual technology stack.
- Explicitly forbidden dependency directions.
- Feature index and infrastructure index.
- Only the most important dependency directions.
- Navigation routes to feature, architecture, module-map, key-files, and infrastructure documents.
- Domain terms, hazards, and commands that were actually discovered.

Do not put complete data flows, exhaustive file lists, full API inventories, or code templates in `overview.md`.

## Phase 4: prepare handoff

For a large codebase or a context-limited session, write a temporary `.compass/context/L1-codebase-map/_handoff.md` containing:

```markdown
# L1 Build Handoff

## Infrastructure
[confirmed component table or `none`]

## Features
[confirmed feature table]

## Cross-feature signals
[recipes, hazards, dependencies, terminology]

## Supplementary context
[relevant user-provided facts or `none`]

## Overview snapshot
[current overview.md]
```

Use `_handoff.md` only to continue into deep analysis. Delete it after the permanent L1 documents are complete and checked, unless the current task must resume later.

## Quality checks

- `overview.md` is a navigation page, not a repository transcript.
- Every indexed feature has a real code entrypoint or an explicit `[待确认]` marker.
- Infrastructure is not mixed into the feature table.
- No example placeholder is presented as project fact.
- Commands were discovered from the project rather than guessed.
- Deep analysis has an explicit feature and infrastructure worklist.
