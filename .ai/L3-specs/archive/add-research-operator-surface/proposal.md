# add-research-operator-surface

> **状态**: archived
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

- `2026-05-10` — `—` → `drafting` by `/new-change` | 原因: 用户要求把下一阶段 plan 拆成多个 changes，并先按业务结构审阅 proposal
- `2026-05-10` — `drafting` → `implementing` by `/new-change` | 原因: 用户确认要直接改结构、合并新旧入口、允许部分成果继续、不保留兼容壳、执行全量迁移
- `2026-05-25` — `pending-review` → `approved` by `/review-tests` | 原因: 全量场景覆盖，所有 7 个 Scenario 均有对应测试，无反模式命中

## Why

当前 workspace 的真实业务流已经是“收集 → 资料库 → 简报 → 交付”，但操作者看到的第一层仍然是 3 个来源工具命令。这会让人继续把系统理解成几个零散工具，而不是一个完整的 research workflow。现在已经不再需要兼容旧入口，而是要把唯一操作者入口直接改成业务动作视角。

## What Changes

- 新增一个 workspace 级的 operator surface，用业务动作组织常用流程：`collect`、`query`、`briefing`、`backfill`
- 合并旧入口与新入口，让操作者只面对一个主命令表面，不再区分“旧来源脚本”和“新业务层入口”
- 为 workspace 根目录补充统一的使用入口和说明文档，让“怎么用这个系统”先于“有哪些来源工具”
- 约定多来源或多动作流程默认允许部分成果继续，并显式输出缺口或失败项
- 把 operator 视角纳入 `.ai` 导航、spec 和 traceability，避免后续继续围绕来源脚本讨论产品能力

## Alternatives Considered

1. **继续只保留来源工具入口** — 改动最小，但业务流仍然散在多个命令和目录里，用户会继续按旧结构理解系统
2. **先保留新旧两套入口并行** — 过渡风险低，但会继续保留双表面，不能真正解决结构与业务不一致
3. **直接补 operator surface 并作为唯一入口（当前选择）** — 一次性把操作者表面切到业务流，旧入口不再继续保留

## Capabilities Affected

### New Capabilities

- `research-operations`: 面向操作者的统一 workspace 入口与命令集合

### Modified Capabilities

- `system`: 系统边界将显式覆盖“操作者如何从根目录运行完整 research workflow”
- `github`: GitHub 能力将作为 collect 动作下的一个来源，而不是独立产品表面
- `papers`: papers 能力将作为 collect 动作下的一个来源，而不是独立产品表面
- `wechat`: WeChat 能力将作为 collect 动作下的一个来源，而不是独立产品表面
- `research-query`: 查询能力将进入统一 operator 流程
- `research-reporting`: 简报能力将进入统一 operator 流程

## Impact

影响范围会落在 repo 根使用入口、workspace README / 命令说明、统一 CLI 或等价入口设计、以及 `.ai` 导航和验证记录。原则上不改变 `output/` 原始归档结构，但会移除旧命令作为对外主入口。

## Review Feedback

- [ ] 暂无

## Known Gaps

- [ ] 暂不包含 Web/TUI；统一 operator surface 先以本地 CLI 完成
