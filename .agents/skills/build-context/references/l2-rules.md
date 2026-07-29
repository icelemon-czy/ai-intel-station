# L2 Rule Discovery

Use this reference to derive project-wide rules, file templates, testing conventions, and module contracts from real code and configuration.

## Contents

- [Evidence policy](#evidence-policy)
- [Phase 1: collect evidence](#phase-1-collect-evidence)
- [Phase 2: global rules](#phase-2-global-rules)
- [Phase 3: file templates](#phase-3-file-templates)
- [Phase 4: testing rules](#phase-4-testing-rules)
- [Phase 5: module rules](#phase-5-module-rules)
- [Quality checks](#quality-checks)

## Evidence policy

- Derive rules from compiler, lint, formatter, build, test, CI, and repeated code patterns.
- Prefer enforced configuration over observed style, and repeated style over a single example.
- Do not convert absence into prohibition. “Module A does not import B” is not proof that the dependency is forbidden.
- Give concrete correct and incorrect examples when the project supplies enough evidence.
- Mark weak or conflicting signals as `[待确认：...]`.
- Never write vague rules such as “keep code clean” or name an architecture pattern without executable constraints.

## Phase 1: collect evidence

Read L1 first:

```bash
cat .compass/context/L1-codebase-map/overview.md
cat .compass/context/L1-codebase-map/module-map.md
```

Inspect files that actually exist:

- Language and package metadata.
- Compiler, lint, formatter, and type-check configuration.
- Build scripts, Makefiles, task runners, and CI commands.
- Representative source files from multiple modules.
- Representative tests and test configuration.
- Public exports and real external callers.
- Recent commits and branch names when version-control conventions matter.

Useful searches include:

```bash
rg -n 'extends Error|class .*Error|class .*Exception|errorHandler|ExceptionHandler' .
rg -n 'eslint-disable|noqa|noinspection|SuppressWarnings' .
rg -n '^export|module\.exports|__all__|^pub ' .
git log --oneline -20 2>/dev/null
git branch -a 2>/dev/null | head -30
```

Adapt patterns and globs to the language. Exclude dependencies, generated files, build outputs, and vendored code.

## Phase 2: global rules

Read `.compass/context/L2-rules/global.md` before editing it.

### Technology and commands

Record exact versions and commands only when supported by checked files. Separate install, development, build, test, lint, formatting, and type-check commands.

### Naming and layout

Sample at least three comparable files before declaring a naming or layout rule. When the repository is inconsistent, describe the dominant convention and mark exceptions rather than fabricating uniformity.

### Dependency direction

Use imports, build boundaries, lint restrictions, and module-map evidence. A useful rule names:

- Source layer or directory.
- Allowed or forbidden target.
- The required interaction mechanism.
- How to verify the rule.
- Why violation matters, when confirmed.

### Error handling

Trace where errors are created, wrapped, logged, translated, retried, or swallowed. Include a minimal project-native example. Do not recommend a new pattern during extraction.

### Validation and configuration

Record where inputs are validated, which library or schema mechanism is used, and whether downstream layers may assume validated data. Record how configuration is loaded and which files must change together.

### Anti-patterns

Turn enforced lint rules, recurring review fixes, explicit comments, and known hazards into concrete prohibitions. Do not infer team policy from one accidental implementation.

## Phase 3: file templates

Read `.compass/context/L2-rules/templates.md`.

For each high-value file type:

1. Select at least three representative, current files.
2. Compare imports, declarations, dependency injection, error handling, exports, and tests.
3. Extract the smallest reusable skeleton.
4. Annotate required extension points and forbidden shortcuts.
5. Name the source examples used to derive the template.

Do not paste application-specific business logic or secrets. If the project has no stable repeated pattern, omit that template.

## Phase 4: testing rules

Read `.compass/context/L2-rules/testing.md` and inspect real test infrastructure.

Establish separately:

- Framework and exact commands for unit, integration, and end-to-end tests.
- File naming and placement.
- Assertion style and test naming.
- Fixture, factory, and test-data construction.
- Mock boundaries and prohibited mocks.
- Database isolation and cleanup.
- External-service strategy.
- UI selector and waiting strategy, if present.
- Coverage commands and exclusions, if configured.

Cross-check test commands against package scripts, CI, and configuration. If they disagree, report the conflict instead of choosing silently.

## Phase 5: module rules

Use `.compass/context/L2-rules/_module-template.md` only for major modules with real module-specific contracts.

For each selected module:

1. Find externally used APIs and their callers.
2. Separate stable public contracts from internal implementation.
3. Identify allowed interaction paths from real imports and explicit architecture rules.
4. Extract module-specific coding and testing patterns.
5. Record module-specific libraries, configuration, and hazards.
6. Mark status and implicit contracts for human confirmation when evidence is insufficient.

Avoid one rule file per directory. Usually 3-8 major module files are enough; small projects may need none.

## Quality checks

- Every rule cites or can point to concrete code/configuration evidence.
- Correct and incorrect examples use project-native syntax.
- `global.md` contains cross-project rules, not module trivia.
- `templates.md` contains patterns derived from multiple files.
- `testing.md` contains commands that were actually checked.
- Module files document contracts and boundaries, not repeat L1 navigation.
- Conflicts and uncertain intent are visible as `[待确认：...]`.
