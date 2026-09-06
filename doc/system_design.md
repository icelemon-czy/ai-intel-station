# System Design

AI Intel Station 只有一条 product pipeline：source data 进入本地 archive，Library 提供统一读取 contract，briefing 派生阅读产物，Agent、CLI 和 optional Web 只是不同 operator surface。各 surface 共享同一 runtime 与 filesystem source of truth，不各自维护 business rule。

```text
project Agent ─→ research CLI ───────┐
direct CLI ──────────────────────────┼─→ shared services
optional Web ─→ adapters/web ────────┘          │
                                               ├─ remote source → collect / discover / seek
                                               │                         │
                                               │                         ↓
                                               └─ query / briefing ← archive + sidecar
                                                                         │
                                                                         ↓
                                                               output/briefing/
```

## Source-of-truth boundary

本页是 architecture 的 source of truth：layer ownership、dependency direction 与当前 **`src/ai_intel_station/` layout**。它不是逐文件 inventory。Refactor 不能用临时 code shape 改写这里的 ownership 和 dependency direction。

| 问题 | Canonical source |
|:-----|:-----------------|
| 项目持续解决什么、从哪里开始操作 | [`README.md`](../README.md) |
| system boundary、layer ownership、dependency direction | 本页 |
| feature 的 intended behavior 与重要 decision | 对应 `doc/*_design.md` |
| current implementation 是否符合 design | code、config、test 与 runtime evidence |

用户确认优先于已有 design。发现 design 与 implementation 冲突时，先记录 conflict；在用户确认前，implementation 不能自动成为新 requirement。

## Architecture invariants

Refactor 必须保持以下 invariant：

1. `research` 是唯一 product CLI；Agent Skill、platform adapter 和 Web surface 不建立第二套 runtime。CLI command 名称保持 `research`，不随 Python package path 收拢到 `src/ai_intel_station/` 而改变。
2. remote fetch 只发生在 collect（含 Interest Sweep `seek`）或 discovery boundary；Library query、generic briefing 和 Web Library 只读取 local archive。
3. `ResearchItem` sidecar 是 collector、Library、briefing 和 Web 共享的数据 contract；source-specific metadata 不要求抹平成中央 database。
4. `output/<source>/` 保存 primary material，`output/briefing/` 保存可重建的 derived artifact，两者不互相冒充。
5. `adapters/web` 只组合 shared service 并维护 HTTP/job boundary；React UI（`frontend/`）不复制 Python business rule。
6. dependency 从 operator adapter 指向 orchestration/service，再指向 domain、filesystem 或 external boundary；Library 与 briefing 不依赖 Web，source adapter 之间不互相调用。
7. project Workflow 只在 `.agents/skills/` 维护 canonical copy；platform-specific Skill 保持 thin adapter。
8. 已退休的 context hierarchy、source-specific standalone CLI 和重复 full Skill copy 不重新进入 repository。

## Layer ownership

| Layer | Ownership | 不负责什么 |
|:------|:----------|:-----------|
| Agent Skills | 解释 user intent，选择已记录的 workflow | 不实现第二套 product runtime |
| `cli`（`research`） | 提供唯一 CLI、解析 command、编排 service | 不拥有 source-specific parsing 或 rendering rule |
| `collect` | 访问 remote source，normalize 并保存 source material | 不执行本地 query 或生成 briefing |
| `library` | 维护 `ResearchItem` contract、sidecar storage、query、backfill 与 archive migration | 不访问 remote source |
| `briefing` | 选择、render、preview 并保存 derived reading artifact；含 Markdown persistence | 不拥有 primary archive |
| `adapters/web` + `frontend` | 将现有 service 暴露为 local HTTP/UI | 不复制 collector、Library 或 briefing business rule |
| `discovery` | 验证 discovery config，编排 source sweep、selection、coverage 与 run log | 不替代 standalone collect 或 generic briefing |

## Repository map

Repository 按 ownership 分区，而不是按每个 command 建一套 vertical stack。开发者扫 root 时先看这些组；`frontend/` 独立于 Python package，不是漏进 `src/` 的业务代码。

### Product source

| Path | Role |
|:-----|:-----|
| `src/ai_intel_station/cli/` | `research` CLI、command orchestration |
| `src/ai_intel_station/discovery/` | Daily Discovery runtime；`schedule/` 下是 `research schedule` 的 packaged launchd/cron template |
| `src/ai_intel_station/collect/` | source adapter |
| `src/ai_intel_station/library/` | ResearchItem / sidecar / query / backfill / migration |
| `src/ai_intel_station/briefing/` | briefing behavior 与 Markdown persistence |
| `src/ai_intel_station/adapters/web/` | Python HTTP adapter（backend + static build artifact） |
| `frontend/` | React UI source 与 Node tests；独立于 Python package，不是漏进 `src/` 的业务代码 |

### Agent surface

| Path | Role |
|:-----|:-----|
| `.agents/skills/` | canonical project Workflow（Daily Discovery、Interest Sweep） |
| `.agents/playbooks/` | one-off source fetch playbook；调用 `research` runtime |
| `CLAUDE.md`、`.claude/skills/`、`.github/*instructions*`、`.github/skills/` | platform adapter |

### Validation / release

| Path | Role |
|:-----|:-----|
| `tests/` | behavior evidence |
| `release/` | wheel/artifact checker 与 installed-wheel smoke |

### Design

| Path | Role |
|:-----|:-----|
| `doc/` | canonical product 与 validation design |

## State 与 artifact boundary

| Path | Lifetime | Ownership |
|:-----|:---------|:----------|
| `src/ai_intel_station/discovery/discovery.yaml.example` | packaged | canonical discovery config example |
| `src/ai_intel_station/discovery/schedule/` | packaged | `research schedule` 的 launchd/cron template |
| `config/discovery.yaml` | local、ignored | operator preference |
| `output/<source>/` | local、ignored | collect / discovery / seek primary material |
| `output/briefing/` | local、ignored | briefing，可重建 |
| `output/briefing/library/` | local、ignored | Library catalog；按 date/tag 浏览并审计 duplicate，不移动 archive |
| `.state/discovery/` | local runtime state | discovery run log |
| `src/ai_intel_station/adapters/web/static/` | packaged build artifact | Web runtime，由 release validation 检查 |

Feature-specific behavior 不在本页重复：collection 与 Library 见 [`research_library_design.md`](research_library_design.md)，每日 discovery 见 [`daily_discovery_design.md`](daily_discovery_design.md)，topic 一次性 sweep 见 [`interest_sweep_design.md`](interest_sweep_design.md)，派生产物见 [`briefing_design.md`](briefing_design.md)，Web boundary 见 [`web_workspace_design.md`](web_workspace_design.md)，验证策略见 [`validation_design.md`](validation_design.md)。
