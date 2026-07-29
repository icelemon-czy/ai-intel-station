# Entrypoint Boundary for Context Setup

Use this reference only when `build-context` must verify the Compass context entrypoint. Skill deployment and platform file generation remain the responsibility of `.compass/INSTALL.md` and the selected platform installer.

## Shared project entrypoint

`.compass/AGENTS.md` is the canonical instructions source. Each selected platform installer merges its managed section into that platform's project-level instruction file using stable markers:

```text
<!-- compass:start -->
...
<!-- compass:end -->
```

The section contains only portable project rules. Do not duplicate detailed context, installation paths, or Skill bodies into the project instruction file. `build-context` reads `.compass/context/` as its own source; Skill discovery uses each selected platform's project-level native Skill directory.

## Platform routing

| Platform | Project instructions | Project Skill directory | Platform installer |
|:---------|:---------------------|:------------------------|:-------------------|
| Codex | Root `AGENTS.md` | `.agents/skills/` | `.compass/platforms/codex/INSTALL.md` |
| Claude Code | Root `CLAUDE.md` | `.claude/skills/` | `.compass/platforms/claude-code/INSTALL.md` |
| OpenCode | Root `AGENTS.md` | `.opencode/skills/` | `.compass/platforms/opencode/INSTALL.md` |

`build-context` must not guess or reproduce platform formats. If an entrypoint is absent or incorrect, report it and execute `.compass/INSTALL.md` only when the user's task includes installation or repair.

## Verification

Check without overwriting user content:

1. The selected platform's project instruction file exists.
2. The Compass marker block appears exactly once in that file.
3. The block contains only shared project rules; it does not route context or Skill discovery.
4. The selected platform's installer has completed its own checks.
5. The selected platform's native Skill directory contains the managed Compass Skills and no Skill symlink.
6. The built-in read-only `sdd-reviewer` exists for each supported selected platform or the installer recorded inline fallback; optional `codebase-explorer` exists only when explicitly selected.

If any of these fail during a context-only request, report the installation problem separately instead of silently changing platform files.
