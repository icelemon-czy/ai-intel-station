# align-ai-context-with-business-architecture

> **状态**: pending-review
> **创建**: 2026-05-10
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0  <!-- 不得 ≥ 2，防止 /fix-bug 递归 -->

## Status Machine（不要删）

```text
drafting ──→ implementing ──→ pending-review ──→ approved ──→ archived
   ↑              ↑  ↑              │
   │              │  └──────────────┘
   │              │   review 打回 (review-failed → implementing)
   │              │
   └──────────────┘
     spec 歧义回退（走 /fix-bug Step 3C）
```

| 状态 | 含义 | 由谁推进 |
|:-----|:-----|:---------|
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal）|
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿）|
| pending-review | review-failed | /review-tests（打回）|
| review-failed | implementing | /fix-bug（开始修）|
| pending-review | approved | /review-tests（通过）|
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-05-10` — `—` → `drafting` by `/new-change` | 原因: 用户要求把业务结构 plan 通过多个 changes 固化到 `.ai` spec 和文档体系中
- `2026-05-10` — `drafting` → `implementing` by `/new-change` | 原因: 用户确认要按新业务结构直接落地，并要求旧入口与旧文档体系一并迁移和收口
- `2026-05-10` — `implementing` → `pending-review` by `/continue-change` | 原因: `.ai` patch artifact 与重复 workflow source-of-truth 已清理，active docs 与 traceability 已对齐

## Why

`.ai` 当前已经部分写成业务结构，但主 spec 仍缺 research-query / research-reporting / operator surface 等正式 capability，且存在镜像 workflow 与历史 patch artifact。这会让文档体系本身变成第二套结构噪音。既然要全量迁移，就不能只改代码而不收口 `.ai` 的 source-of-truth。

## What Changes

- 为 `research-query`、`research-reporting`、`research-operations`、`workspace-entrypoint-topology` 等业务能力补齐主 spec 能力域与 traceability
- 清理 `.ai` 中残留的 patch artifact 文本，避免模板片段继续污染系统 spec / rules / validation 文档
- 明确 `.github/` 与 `.ai/.github/` 等镜像目录的角色，定义单一 source of truth；若镜像无必要则直接移除
- 将 feature / module / validation 文档统一成“业务层优先、operator surface 优先、来源能力次之”的导航方式

## Alternatives Considered

1. **继续增量补文档，不处理旧噪音** — 成本小，但结构漂移会继续累积，spec 很快会失去可信度
2. **整份 `.ai` 从头重建** — 最彻底，但风险高，且会丢掉已有演进历史和可追溯性
3. **按业务结构做定向校准并清理旧镜像（当前选择）** — 保留已有积累，同时把 source of truth 和业务层次重新拉直

## Capabilities Affected

### New Capabilities

- `research-operations`: 业务层 operator surface 的正式 spec 和验证记录

### Modified Capabilities

- `system`: 系统级需求需要正式承认业务层能力域和 `.ai` source-of-truth 规则
- `research-query`: 从 change 内 capability 升格为主 spec 中的正式能力域
- `research-reporting`: 从 change 内 capability 升格为主 spec 中的正式能力域
- `workspace-entrypoint-topology`: 从 change 内 capability 升格为主 spec 中的正式能力域
- `archive-output`: 输出边界文档和验证记录要反映原始归档与派生产物的双层结构

## Impact

影响范围主要在 `.ai/L1`、`.ai/L3`、`.ai/L5`、workflow 镜像目录和校验规则；会直接影响运行时文档入口、校验规则和目录 source-of-truth，但不改变原始归档数据本身。

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 若仍需保留 `.ai/.github` 镜像，必须补清晰用途说明；否则应直接移除
