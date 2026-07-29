# Agent-first Daily Intelligence

> **状态**: archived
> **创建**: 2026-07-25
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
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 +代码实施中 | AI |
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

- `2026-07-25 13:10` — [无] → [drafting] by /develop | 原因: user 确认 Agent-first 为 primary interface，开始最小 daily intelligence slice
- `2026-07-25 16:46` — [drafting] → [implementing] by /develop | 原因: sdd-reviewer 多次超时后由 Main Agent 按 validation rules 完成 plan review；scope 无业务歧义，补充 optional-import anti-overfit test 后进入 TDD
- `2026-07-25 17:49` — [implementing] → [pending-review] by /develop | 原因: core-only bootstrap、62 个 Agent/discovery tests、14 个 runner tests、36 个 WeChat/sidecar tests 与 fresh-context Today forward test 通过；L2/L5 已同步，进入只读 verify
- `2026-07-25 17:55` — [pending-review] → [review-failed] by /develop | 原因: sdd-reviewer 取得 direct evidence 后仍超时；Main Agent fallback review 发现 fresh-context Agent 未把 dry-run 与真实 today artifact 明确区分，未执行或请求 network run
- `2026-07-25 17:55` — [review-failed] → [implementing] by /develop | 原因: 开始收紧 Today decision rule 并补 fresh-context anti-overfit forward test
- `2026-07-25 17:58` — [implementing] → [pending-review] by /develop | 原因: Skill contract tests 4/4 通过；第二次 fresh-context test 正确拒绝将 dry-run/旧 briefing 当作 today artifact，在 network approval 不可用时明确返回 local fallback
- `2026-07-25 17:59` — [pending-review] → [approved] by /develop | 原因: sdd-reviewer 超时后 Main Agent 按 validation-rules 完成 fallback verify；真实 call path、assertion、62+14+36 tests、core bootstrap 与修复后 forward test 支持 PASS，两个 partial 作为 non-blocking gap 保留
- `2026-07-25 18:00` — [approved] → [archived] by /develop | 原因: delta 已合并到 daily-discovery、research-operations 与 wechat main Specs；business Spec structure 验证 55 Requirements / 64 Scenarios，无 incomplete 或 duplicate Requirement

## Why

当前 daily-discovery Skill 仍把 CLI、YAML 和 log 操作交给 user；同时 fresh core
environment 会解析 51 个 packages，包括默认关闭的 WeChat browser stack。Agent-first
入口如果不能自己完成 setup/run/read，且 GitHub/Papers 也必须安装 Camoufox，就没有真正减轻
首次使用成本。

## What Changes

- 将 `daily-discovery` 改成 Agent-operated Workflow：Agent 执行 setup/run/status、
  读取 briefing 并直接返回最多 5 条重点。
- 保持 Python `research` runtime 为 deterministic source of truth；Skill 不复制业务逻辑。
- 将 base dependency 收敛为 core discovery 所需依赖，把 WeChat browser stack 移到
  `wechat` optional extra，把 pytest 移到 `dev` optional extra。
- 在缺少 WeChat extra 时返回明确、可执行的安装 guidance，不输出 Python traceback。
- 冻结 Web 为 optional viewer；本 change 不重做或删除 Web。

## Alternatives Considered

1. **继续 Web-first** — 已有功能可复用，但没有解决表单、配置与启动成本，且会继续复制 operator flow。
2. **只改 Skill，不拆 dependency** — 对话入口更自然，但首次运行仍下载 51 个 packages，Agent 无法轻量启动。
3. **Agent-first + lightweight core（当前选择）** — 复用现有 runtime，默认只承担 GitHub/Papers/briefing 成本，WeChat 按需安装；scope 可逆且不删除 Web。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- `daily-discovery`: Agent 直接完成今日情报、preference、status 与明确请求的 schedule。
- `research-operations`: core command surface 不再依赖 optional WeChat/browser 或 test stack。
- `wechat`: 缺少 optional runtime 时返回明确安装 guidance。

## Impact

- Agent routing: `.agents/skills/daily-discovery/SKILL.md`、`AGENTS.md`
- Packaging: `pyproject.toml`、`uv.lock`
- Runtime error boundary: `collect/wechat.py`、`research/cli.py`
- Tests: lightweight dependency boundary、core CLI smoke、WeChat missing-extra guidance
- Docs/context: install guidance、CLI runtime、external dependency map、L5 traceability

## Review Feedback

- Blocking（已修复）：第一次 fresh-context Today test 能诚实说明没有今日新内容，但把
  dry-run 作为停止依据，未进入真实 run / network permission 分支。Skill 必须明确：
  dry-run log、`(dry-run)` briefing 与空 briefing 都不是今日可用 artifact。
- 修复 evidence：第二次 fresh-context test 明确返回“今天没有可验证的新情报结果”，将
  旧库存标为非今日参考；未启动 Web，未要求 user 操作 CLI/YAML/log。

## Known Gaps

- [ ] CLI structured JSON contract 不在本 change；先用稳定 Summary / artifact path 完成 Agent Workflow。
- [ ] Web information architecture 将在 Agent-first dogfood 后重新 design，本 change 只冻结其 primary-interface 地位。
- [x] optional WeChat full install 已于 2026-07-27 闭合：实际安装 44 packages，
  runtime import 成功，相关 tests 通过，随后恢复 default core。
- [x] first-run preference write 已于 2026-07-27 通过 isolated fresh-context forward test：
  parsed config comparison 证明只修改目标 search，其他 field 与 private URL 保持不变。
