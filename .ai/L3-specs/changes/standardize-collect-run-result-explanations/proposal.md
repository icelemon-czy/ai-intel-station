# Standardize Collect Run Result Explanations

> **状态**: approved
> **创建**: 2026-06-01
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

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

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建 collect 运行结果解释标准化 proposal，等待业务确认
- `2026-06-01 14:40` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进
- `2026-06-01 15:10` — [implementing] → [pending-review] by /continue-change | 原因: 6 个新测试全绿 + 62/62 tests/test_web_workspace.py 绿灯

## Why

Collect Workspace 运行完成后当前更偏向展示原始 JSON payload，用户不容易快速判断本次运行是否成功、写入了什么、下一步应该去哪里看结果。

本变更将 collect run result 标准化为人类可读摘要，同时保留必要的技术细节用于排查。

## What Changes

- Collect 成功时展示统一摘要：source、运行状态、收集 / 写入数量、保存路径或可查看位置、推荐下一步。
- Collect 部分成功或失败时展示明确解释：失败来源、可理解的错误信息、建议检查输入或外部依赖。
- JSON payload 可继续保留，但应降级为技术细节区域，不作为主要结果说明。
- 成功结果应继续提供去 Library 查看本地资料的动作入口。
- 不改变 `run_collect()` 的真实执行结果语义，不改变输出目录，不新增 job history 或后台队列。

## Alternatives Considered

1. **只展示 JSON payload** — 对开发调试直接，但对使用者理解成本高。
2. **完全隐藏 JSON payload** — 页面更干净，但排查失败时会丢失上下文。
3. **人类可读摘要 + 技术细节保留（当前选择）** — 兼顾日常使用和调试可见性。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `research-web-workspace`: Collect Workspace 应在运行结束后展示标准化、可操作的人类可读结果说明。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- 服务层 payload：若当前 `run_collect()` 缺少统一字段，可在 `workspace_web/service.py` 中补齐不破坏现有字段的摘要字段。
- 回归测试：`tests/test_web_workspace.py` 可增加成功、失败和技术细节展示的断言。
- 不涉及真实采集逻辑、外部依赖调用、输出文件格式或数据迁移。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] 不新增历史运行记录；job timeline 另行处理。
- [ ] 不实现自动重试、排队执行或 scheduled collection。
