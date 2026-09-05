# Source-Tree Migration Todo

本清单只跟踪当前 **source-tree 整理**（把散落在 repository root 的 Python source 收拢到 `src/ai_intel_station/`），不定义永久 product behavior，也不回顾已完成的 archive migration。Target architecture 以 [`system_design.md`](system_design.md) 为准；全部完成后删除本文件。

## Target outcome

1. 全部 Python source 收拢到 `src/ai_intel_station/`。**tracked product/source tree** 只留 `src/`、`web/`（React frontend）、`tests/`、`scripts/`、`tools/`、`doc/` 与配置文件；`.agents/` 与 platform adapter 保持 thin。`output/`、`.state/`、`config/`（以及待确认的 `.obsidian/`）作为 intentional local/runtime directory 保留，不计入 tracked source 清洁度。
2. `publish` 合并进 `briefing`（Obsidian persistence 成为 briefing 的一部分）。
3. `workspace_web` backend 移到 `adapters/web`；React `web/` 保持独立。
4. `.agents/` 保持 canonical Workflow；platform-specific directory 只保留 thin reference。
5. 移除 empty / noise directory 与生成 cache；tracked tree 干净，ignored local dependency/runtime directory 不被误判为架构缺陷。
6. `research` CLI command 名称不变，尽管 Python package path 改变。

## Current vs. target gap

| Current root package | Target |
|:---------------------|:-------|
| `research/`（`cli.py` + `commands.py`） | `src/ai_intel_station/cli/` |
| `research/discovery/` | `src/ai_intel_station/discovery/` |
| `collect/` | `src/ai_intel_station/collect/` |
| `library/` | `src/ai_intel_station/library/` |
| `briefing/` + `publish/` | `src/ai_intel_station/briefing/`（publish 并入） |
| `workspace_web/`（backend + `static/`） | `src/ai_intel_station/adapters/web/` |
| `web/`（React） | `web/`（不变，保持在 root） |

Root 现存噪声：`.DS_Store`（root 与 `.claude/`）、`.pytest_cache/`、各 `__pycache__/`；`config/` 仅含 ignored `discovery.yaml`。

## Confirmed decisions

- Source 一律进 `src/ai_intel_station/`；不使用多个顶层 Python package。
- CLI command 保持 `research`；console entrypoint 指向新 package，不新增第二个 command。
- `publish` 合并进 `briefing`，不保留独立 `publish` layer。
- `output/`、`.state/`、`config/` 是 local data / runtime boundary，本次 **不移动、不删除**。
- archive layout 与 output data **已定型**，本次 source-tree 移动 **不得改动**任何 `output/` 内容（这是硬约束，不是待办）。
- `.venv/`、`web/node_modules/` 是 ignored local dependency，不属于 repository architecture；可清理/重建/隐藏，但其存在不算 tracked-tree 失败。

## Decision gate（未确认，禁止删除）

- **`.obsidian/` ownership 未确认。** 需先决定：repository 是否作为 intentional Obsidian vault（保留 `.obsidian/` 在 root），还是把 vault config 移到 `output/` 或另一个显式 vault root。确认前 **禁止删除或移动** `.obsidian/`。

## Safe ordered migration plan

当前 working tree 已含数百个未提交 refactor change，必须先建立可恢复 checkpoint，再做批量 `git mv` / import rewrite。**禁止** `git reset --hard`、`git checkout --` 等 destructive 操作。

1. **P0 — baseline 与 checkpoint（第一个执行 gate）。** 审阅并记录当前 dirty worktree（`git status` + 未提交 change 清单）。建立一个可恢复 checkpoint，**显式捕获全部当前 tracked change、deletion 与 untracked replacement source/docs**——优先新建一个专用 WIP 分支并做一次 WIP commit，或另一个已验证可恢复的 snapshot；确认之后任何批量改动都能回退。**禁止**用 `git stash`（可能遗漏 untracked file），**禁止** `git reset` / `git checkout` 等 destructive 操作；checkpoint 本身不移动、不删除 `output/` 与 `.state/`。
2. **P1 — 建立 `src/ai_intel_station/` 骨架** 并 `git mv` 移动 source（`collect`、`library`、`briefing`+`publish`、`research/cli`+`commands`、`research/discovery`、`workspace_web`→`adapters/web`）；保留 `web/` 在 root。
3. **P2 — import / entrypoint rewrite。** 将 `briefing|collect|library|publish|research|workspace_web` 的 import 改为 `ai_intel_station.*`；更新 pyproject packaging 与 console script（见下）。
4. **P3 — publish→briefing 合并** 与 CLI/discovery/adapters 归位（见专项）。
5. **P4 — platform adapter 与 root 清理。** `.claude`、`.github`、`tools` 保持 thin；移除 empty `.codex/` 目录（见 platform adapter cleanup）；移除 empty/noise directory 与生成 cache（不动 `.obsidian` decision gate）。
6. **P5 — focused validation gates** 与 exit criteria。

## Packaging / import / entrypoint strategy

- `[tool.setuptools.packages.find]` 改为 `where = ["src"]`、`include = ["ai_intel_station*"]`。
- `[project.scripts]` 改为 `research = "ai_intel_station.cli:console_main"`；command 名称保持 `research`。
- package-data 随路径更新：`ai_intel_station.discovery` 的 `discovery.yaml.example`、`ai_intel_station.adapters.web` 的 `static/`。
- 全部 `from <pkg> import ...` 与 `import <pkg>` 改为 `ai_intel_station.<pkg>`；tests 与 `scripts/` 同步。

## 专项

### publish → briefing merge
- 把 `publish/obsidian.py`（`write_markdown`、`briefing_output_path` 等）并入 `src/ai_intel_station/briefing/`，成为 briefing 的 Obsidian persistence。
- 更新 `library/catalog.py`、briefing 与 web 里对 `publish.obsidian` 的 import。

### research CLI + discovery placement
- `research/cli.py` + `research/commands.py` → `src/ai_intel_station/cli/`（parser、dispatch、user-facing exit behavior）。
- `research/discovery/` → `src/ai_intel_station/discovery/`（config、schema/validation、sources、runner、log、scripts）。

### workspace_web → adapters/web
- backend（`service.py`、`server.py`、feature module）→ `src/ai_intel_station/adapters/web/`；`static/` build artifact 随行，由 release validation 检查。
- React `web/` 保持在 root，独立于 Python source。

### frontend web/ boundary
- `web/`（`src/`、`test/`、`vite.config.js`、`package.json`）不进入 `src/ai_intel_station/`；仅 `web/node_modules/` 属 ignored 本地依赖。

### platform adapter cleanup
- `.agents/skills/` 保持 canonical；`CLAUDE.md`、`.claude/skills/`、`.github/*instructions*` 只保留 thin reference，不复制完整规则。
- 当前 `.codex/agents` 与 `.codex/hooks` 均为空，**移除这些 empty `.codex/` 目录**；将来只有当 Codex adapter 有明确的 thin-reference owner 时才保留，不为了对称而保留 empty platform directory。

### generated / cache / empty-dir cleanup
- 移除 `.DS_Store`、`.pytest_cache/`、`__pycache__/` 与空目录；这些是生成物，不进 tracked tree。

## Local data / ignored directory handling（不得误删）

| Path | 类别 | 本次处理 |
|:-----|:-----|:---------|
| `output/` | user data（archive） | 不移动、不删除、不改内容 |
| `.state/` | runtime state | 不移动、不删除 |
| `config/` | operator preference（ignored） | 保留 |
| `.obsidian/` | **待确认**（见 decision gate） | 确认前禁止删除 |
| `.venv/` | ignored local dependency | 可清理/重建，不算架构缺陷 |
| `web/node_modules/` | ignored local dependency | 可清理/重建，不算架构缺陷 |

区分 **tracked repository cleanliness**（`src/`、`web/`、`tests/`、`doc/` 等应干净）与 **ignored local dependency/runtime directory**（上表，其存在不是 tracked-tree 失败）。

## Tests 与 rollback boundary

- tests 一律使用 temporary output root，不依赖 repository 真实 `output/`（conftest `protect_repository_archive` 已保证）。
- source-tree 移动同样要先有 checkpoint（P0），任何批量 `git mv`/import rewrite 后都能回退；发现破坏即回退到 checkpoint。

## Focused validation gates

- packaging/import：`uv sync --frozen`、`python -c "import ai_intel_station"`、`research --help` 可用。
- behavior：focused contract test（archive migration、collector layout）仍绿；不要求本阶段跑完整 release/optional/Web suite。
- cleanliness：tracked tree 无残留旧顶层 Python package、无 `.DS_Store`/cache；`.venv`/`node_modules`/`output`/`.state`/`.obsidian` 按上表处理。

## Exit criteria

- root 不再有 `briefing/`、`collect/`、`library/`、`publish/`、`research/`、`workspace_web/` 顶层 package。
- `import ai_intel_station` 成功，`research` command 可用，console entrypoint 指向新 package。
- `output/`、`.state/`、`config/`、`.obsidian/`（decision gate 前）保持原样。
- tracked tree 干净；无未解释的 file deletion 或 data loss。
