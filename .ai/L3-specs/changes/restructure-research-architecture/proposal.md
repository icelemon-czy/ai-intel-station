# restructure-research-architecture

> **状态**: pending-review
> **创建**: 2026-05-10
> **父变更** (parent-change): add-research-item
> **嵌套深度** (depth): 1  <!-- 不得 ≥ 2，防止 /fix-bug 递归 -->

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
| :--- | :--- | :------- |
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
| :-- | :-- | :--------- |
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal） |
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿） |
| pending-review | review-failed | /review-tests（打回） |
| review-failed | implementing | /fix-bug（开始修） |
| pending-review | approved | /review-tests（通过） |
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-05-10` — `—` → `drafting` by `/new-change` | 原因: 用户要求为代码结构调整、Obsidian 阅读层定位与未来 roadmap 建立 L3 级提案
- `2026-05-10` — `drafting` → `implementing` by `/new-change` | 原因: 用户确认第一阶段不含 Web/TUI，时间为可选条件，报告允许部分成功但必须明确标注缺失来源，并要求继续完成 L3 规格化
- `2026-05-10` — `implementing` → `pending-review` by `/continue-change` | 原因: collect / library / briefing / publish 已落地，兼容层、查询、简报、backfill 与最小 smoke 验证已通过

## Why

现在这套代码更像 3 个分开的抓取脚本：GitHub 一套、papers 一套、wechat 一套。这个结构对“先抓下来存着”是够用的，但对下一步“按主题找资料、按条件筛选、自动生成简报给 Obsidian 看”会越来越别扭，因为这些逻辑会被迫散落到 3 个脚本里。

既然你已经明确 Obsidian 主要是阅读层，不是交互层，这次变更就应该先把代码结构改成更贴业务的样子：前面负责收集，中间负责整理和研判，最后负责把结果交付给 Obsidian。

## What Changes

- 重新定义目标代码结构，用更贴业务的 4 层来组织仓库：`collect/`、`library/`、`briefing/`、`publish/`
- 规划现有 GitHub / papers / wechat 代码如何逐步迁到新结构里，同时保持现有命令和现有 `output/` 结构兼容
- 明确 Obsidian 的角色是“阅读与沉淀”，这次变更不把 Web/TUI 交互层放进第一阶段范围
- 把“查询、时间过滤、报告生成”作为下一阶段真正面向使用的能力写进 roadmap
- 为后续实现准备 delta spec，避免继续把业务逻辑直接堆到各抓取脚本中

## Alternatives Considered

1. **继续维持现在的脚本布局，只额外补几个聚合脚本** — 改动最小，但以后查询、筛选、简报逻辑还是会分散在多个地方
2. **直接先做 Obsidian 插件** — 离使用场景近，但会过早把系统绑死在 Obsidian 里，底层能力还没稳就先做展示层
3. **先把代码改成“收集 → 资料库 → 简报 → 交付”的业务结构（当前选择）** — 先把核心能力和展示方式拆开，后续 Obsidian 只是其中一个交付出口

## Capabilities Affected

### New Capabilities

- `research-query`: 基于统一 `ResearchItem` 的跨来源查询与过滤入口
- `research-reporting`: 生成适合 Obsidian 消费的周报、专题页、阅读清单等 Markdown 产物

### Modified Capabilities

- `github`: 从单纯 repo/search 抓取扩展为“收集层”的一个来源模块
- `papers`: 从按类别抓取脚本扩展为“收集层”的一个来源模块
- `wechat`: 从文章抓取脚本扩展为“收集层”的一个来源模块
- `archive-output`: 从“原始归档目录”扩展为“原始归档 + 面向 Obsidian 的简报产物”两类输出边界
- `system`: 系统边界将从“本地抓取并存 Markdown”扩展到“本地收集、整理、查询、出简报”

## Impact

影响范围会跨越仓库目录结构、模块边界、现有 CLI 兼容层、输出目录约定、`.ai` 导航以及验证策略。按你的要求，这次会尽量守住 3 个约束：

- 现有命令继续可用
- 现有 `output/` 目录结构继续兼容
- 现有历史 Markdown 和 sidecar 可以继续复用

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 本提案暂不包含 Web/TUI 交互层；是否以后单独做，放到后续 change 再定
<!-- End of proposal -->
<!-- EOF -->
