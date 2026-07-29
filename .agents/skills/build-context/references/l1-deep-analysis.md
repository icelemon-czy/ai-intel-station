# L1 Codebase Deep Analysis

Use this reference after L1 discovery to construct feature documentation, infrastructure documentation, runtime architecture, module contracts, coupling maps, and cross-feature task recipes.

## Contents

- [Preparation](#preparation)
- [Phase 1: analyze infrastructure](#phase-1-analyze-infrastructure)
- [Phase 2: analyze each feature](#phase-2-analyze-each-feature)
- [Phase 3: build runtime architecture](#phase-3-build-runtime-architecture)
- [Phase 4: build module map](#phase-4-build-module-map)
- [Phase 5: build key-files](#phase-5-build-key-files)
- [Verification](#verification)

## Preparation

Read:

1. `.compass/context/L1-codebase-map/overview.md`.
2. Temporary `_handoff.md` when present.
3. `.compass/context/L1-codebase-map/features/_feature-template/README.md`.
4. `.compass/context/L1-codebase-map/infrastructure/_infrastructure-template/README.md`.

Build infrastructure before features because shared mechanisms explain feature behavior.

## Phase 1: analyze infrastructure

Skip this phase when discovery confirmed that no distinct shared infrastructure exists.

For each component:

1. Read representative source and configuration files.
2. Find real consumers with `rg` over imports, registrations, dependency injection, or calls.
3. Trace initialization order, public extension points, failure behavior, and configuration sources.
4. Identify non-obvious change propagation and known hazards.
5. Create `.compass/context/L1-codebase-map/infrastructure/<component>/README.md` and layer files only when the component has meaningful internal layers.

Use project vocabulary such as `config-loader`, `plugin-host`, `event-bus`, or `test-runtime`; avoid generic names such as `logic` or `data`.

Each component README should answer:

- What uses this component?
- How is it initialized and configured?
- Which interfaces are stable for callers?
- What must change together?
- What failures degrade operation versus stop startup?

## Phase 2: analyze each feature

For every confirmed feature:

1. Read its entrypoint.
2. Follow one or two primary call paths through actual source files.
3. Identify layers using the project's own concepts.
4. Find external systems, shared infrastructure, persistence boundaries, events, and error paths.
5. Identify changes that require non-obvious updates elsewhere.
6. Write a feature README and only the layer files that materially improve navigation.

### Feature analysis worksheet

| Question | Evidence required |
|:---------|:------------------|
| Where does the feature enter? | Route, command, event, job, UI action, or public API registration |
| What are its real layers? | Read representative files and follow calls |
| What data crosses layer boundaries? | Function signatures, schemas, messages, or persistent models |
| What infrastructure does it use? | Imports, injected dependencies, middleware, or runtime calls |
| What must change together? | Multiple implementations, generated types, fixtures, docs, migrations, or config |
| What can fail? | Error handling, retries, transaction behavior, fallbacks, or cleanup |

### Feature output

Follow the current feature template. At minimum, `features/<feature>/README.md` should contain:

- A layered navigation table with load conditions.
- One or two end-to-end data flows.
- A non-obvious change-impact table.
- Known hazards and unresolved questions.

Layer files should contain key files, interfaces, common modification scenarios, and traps. Do not repeat the README in every layer file.

### Optional delegation

Default to the current Agent. Delegate a feature only when all of these are true:

- The user explicitly requested Subagent use.
- The selected platform has installed the requested role.
- The feature can be analyzed independently.
- The parent Agent can review all returned evidence before writing project facts.

Use `codebase-explorer` for bounded read-only exploration. Do not require one Subagent per feature, and do not let delegated output become fact without parent verification.

## Phase 3: build runtime architecture

Read the current `architecture.md` template. Fill the sections supported by the project:

- Deployment topology and process boundaries.
- Startup and initialization order.
- Representative request, event, job, or message lifecycle.
- Feature-to-infrastructure runtime collaboration.
- Middleware or interceptor order when order affects behavior.
- Error propagation and retry/fallback behavior.
- Runtime configuration that materially changes behavior.

Distinguish runtime collaboration from source-level imports. Put runtime behavior in `architecture.md`; put static module dependencies in `module-map.md`.

## Phase 4: build module map

Read the current `module-map.md` template and inspect real import/export relationships.

Record:

- Main modules and externally used APIs.
- Stable versus internal interfaces, based on actual callers.
- Dependency topology and forbidden directions.
- Non-obvious change coupling.
- Shared code rules and migration constraints.

Do not label an API stable merely because it is exported. Check whether external modules call it and mark uncertain stability for confirmation.

## Phase 5: build key-files

Read the current `key-files.md` template. Add only recurring, cross-feature tasks or investigation starting points.

A useful recipe includes:

1. A representative implementation to copy conceptually.
2. Ordered files or components to change.
3. Required generated artifacts, migrations, registrations, or configuration.
4. Real verification commands discovered from project configuration.
5. Easy-to-miss follow-up work.

Feature-specific recipes belong in the corresponding feature documents.

## Verification

- Every indexed feature has a corresponding document or an explicit reason it does not need one.
- Feature navigation tables link to files that exist.
- Data flows were traced through source rather than inferred from directory names.
- `architecture.md` describes runtime behavior; `module-map.md` describes code dependencies.
- Change-impact tables contain non-obvious coupling, not generic advice.
- `key-files.md` uses real project examples and commands.
- Temporary `_handoff.md` is removed after permanent documents are verified, unless resumable state is needed.
