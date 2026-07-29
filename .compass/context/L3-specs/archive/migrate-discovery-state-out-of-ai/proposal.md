# Migrate Discovery Runtime State Out Of AI Context

> **状态**: archived
> **创建**: 2026-07-25
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

## Status Machine（不要删）

```
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
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项（技术问题或未解决的产品语义），记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /develop |
| drafting | implementing | /develop（必要业务决策完成 + plan review）|
| implementing | pending-review | /develop（相关测试全绿）|
| pending-review | review-failed | /develop（SDD review BLOCKED）|
| review-failed | implementing | /develop 或 /fix-bug（开始修复或落实已确认决策）|
| pending-review | approved | /develop（SDD review PASS）|
| approved | archived | /develop（自动合并并验证）|

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-07-25 00:00` — [无] → [drafting] by /develop | 原因: `.ai` 迁移审计确认 runtime log 与 agent context 混放
- `2026-07-25 09:32` — [drafting] → [implementing] by /develop | 原因: plan review PASS；legacy、retention、cron 与 Web config 语义已闭合
- `2026-07-25 09:36` — [implementing] → [pending-review] by /develop | 原因: migration 5/5、相关 Python 28/28、Node discovery/Web build 通过；L2 与 doc-sync 检查完成
- `2026-07-25 09:40` — [pending-review] → [approved] by /develop | 原因: Main Agent verify PASS；reviewer verify 回合 timeout，按 validation-rules 复核 diff、Scenario evidence 与已知 gaps
- `2026-07-25 09:41` — [approved] → [archived] by /develop | 原因: delta 已合并到 daily-discovery 主 Spec，结构与 traceability 验证完成

## Why

daily discovery 当前把 run log 默认写入 `.ai/L4-session/discovery/`，导致 runtime state 与 agent-facing context 耦合，也让旧 `.ai` 无法安全退役。

## What Changes

- 默认 discovery state directory 改为 repository-local `.state/discovery/`
- example config、schedule script、Web hint 与 user documentation 使用同一默认路径
- 自定义 `log_dir` 继续有效；旧 config 中显式的 `.ai/L4-session/discovery` 也继续按自定义路径处理
- migration 本身不删除或搬迁旧 log；若旧目录仍是 active `log_dir`，原有 `max_log_files` retention 继续生效
- generated cron 在 fresh checkout 中先创建 state directory，再启动 discovery
- Web run 使用请求所选 config 解析出的 `log_dir`，不再被 repository default config 覆盖

## Alternatives Considered

1. **继续使用 `.ai/L4-session/discovery/`** — 无兼容迁移，但 agent context 会继续混入 runtime state
2. **默认改为 `.state/discovery/`（当前选择）** — 明确区分 product state 与 Compass context，同时保留自定义路径兼容性
3. **把旧模板精确值自动解释为新 default** — 会覆盖用户显式配置，也改变 retention 作用目录；本次选择兼容优先
4. **自动移动旧 log** — 会修改 user data，且 status 读取跨目录的兼容语义更复杂，本次不做

## Capabilities Affected

### Modified Capabilities

- `daily-discovery`: persistent run log 的默认 state directory 与迁移行为

## Impact

影响 `research/discovery/config.py`、schedule helper、`workspace_web/service.py`、example config、Web 提示、tests 与相关 docs。没有 API schema 或 dependency 变化。

## Review Feedback

- 无

## Known Gaps

- 旧 config 若继续显式使用 `.ai/L4-session/discovery/`，需要 operator 手动改成 `.state/discovery/` 才会切换目录。
