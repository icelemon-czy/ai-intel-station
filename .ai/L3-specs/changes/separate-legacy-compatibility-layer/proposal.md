# separate-legacy-compatibility-layer

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
| :----- | :----- | :--------- |
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
| :--- | :--- | :------------ |
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal） |
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿） |
| pending-review | review-failed | /review-tests（打回） |
| review-failed | implementing | /fix-bug（开始修） |
| pending-review | approved | /review-tests（通过） |
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-05-10` — `—` → `drafting` by `/new-change` | 原因: 用户要求把代码结构继续按业务层清晰化，并把旧入口从主结构中分离出来
- `2026-05-10` — `drafting` → `implementing` by `/new-change` | 原因: 用户确认不保留兼容壳，而是直接把旧入口合并进新的业务入口并完成全量迁移
- `2026-05-10` — `implementing` → `pending-review` by `/continue-change` | 原因: 旧 runtime wrapper 已删除，根级打包与测试表面已迁到统一入口，旧来源参考资料已收口到 `tools/`

## Why

`collect/`、`library/`、`briefing/`、`publish/` 已经形成核心业务层，但 `github-tools/`、`papers-tools/`、`wechat-article-to-markdown/`、`research_item.py` 仍然占据仓库主表面。这会让贡献者继续从旧入口开始读和改代码，而不是从核心层开始。既然已经决定不做兼容，这一层就不应该继续存在。

## What Changes

- 将旧入口的职责直接合并到新的 operator surface 和核心业务层，不再保留单独 compatibility / adapters 边界
- 删除旧入口文件和旧入口导向的测试锚点，避免未来业务逻辑重新回流到来源脚本目录
- 统一打包和运行方式，让核心代码与对外命令表面完全一致
- 在不破坏现有输出布局和已有归档数据的前提下，完成代码和测试层面的全量迁移

## Alternatives Considered

1. **保持现状，只靠文档提醒哪些是旧入口** — 实现成本最低，但代码表面仍然会误导贡献者
2. **显式分出 compatibility layer 再长期保留** — 过渡更温和，但仍会保留双表面和长期结构负担
3. **直接合并旧入口并移除 compatibility path（当前选择）** — 一次性完成结构收口，让仓库表面和业务结构一致

## Capabilities Affected

### New Capabilities

- `workspace-entrypoint-topology`: 对 workspace 唯一入口、目录职责和迁移边界的正式治理能力

### Modified Capabilities

- `system`: 系统边界将明确只保留一个 operator surface，对外不再暴露来源脚本入口
- `github`: GitHub 操作将被纳入统一 operator surface，而不是单独来源脚本入口
- `papers`: papers 操作将被纳入统一 operator surface，而不是单独来源脚本入口
- `wechat`: WeChat 操作将被纳入统一 operator surface，而不是单独来源脚本入口
- `research-query`: backfill/query 将被纳入统一 operator surface，而不是独立兼容脚本

## Impact

影响范围会落在 top-level 目录职责、打包元数据、README / SKILL 文档，以及 `.ai` 模块地图。该变更不再保持旧命令兼容，但必须保持旧输出路径和历史 sidecar 数据可继续工作。

## Review Feedback

- [x] 用户指出 repo root 仍保留旧来源目录表面；已补齐 `tools/` 收口与 repo-topology 测试后重新进入待审

## Known Gaps

- [ ] 若某些外部脚本或个人习惯仍依赖旧命令，需要在变更说明中明确这是 BREAKING 迁移
