# 将 WeChat 降级为 optional News mix

> **状态**: archived
> **创建**: 2026-08-15
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
| `review-failed` | Review 有阻塞项，记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 转移日志（append-only）

- `2026-08-15 08:48` — [无] → drafting by /develop | 原因: user 要求 WeChat 从 required minimum 降级为 optional two-item mix，并同步现有 Codex daily automation
- `2026-08-15 08:55` — drafting → implementing by /develop | 原因: plan review PASS，attempted-source matrix、legacy migration、cap shortfall 与 automation read-back contract 已明确
- `2026-08-15 09:07` — implementing → pending-review by /develop | 原因: production-path tests、467-test core regression、WeChat suite、L3 checks、dry-run 与 automation read-back 全部通过
- `2026-08-15 09:12` — pending-review → review-failed by sdd-reviewer | 原因: explicit zero minimum 被错误迁移为 whole-lane maximum，且 optional maximum 不要求 WeChat source 的 Scenario 缺少 assertion
- `2026-08-15 09:12` — review-failed → implementing by /develop | 原因: 补 migration boundary 与 optional-source validation anti-overfit test
- `2026-08-15 09:13` — implementing → pending-review by /develop | 原因: 两个 verify gap 已先 red 后修复；91 targeted 与 469 core regression 通过
- `2026-08-15 09:16` — pending-review → approved by sdd-reviewer | 原因: re-review PASS；delta contract、implementation、tests、automation read-back 与 execution evidence 完整一致
- `2026-08-15 09:16` — approved → archived by /develop | 原因: delta 已合并主 Specs，L1/L2/L5 已同步，validation report 与 traceability 已更新

## Why

WeChat public index 不能稳定提供 realtime coverage，当前 default `wechat_min_items=2` 会让已完整的 HN/GitHub/arXiv briefing 因微信缺失而长期 `partial`。Daily automation 仍写着旧的“最多 5 条”说明，也没有反映 5 News + 1 GitHub + 1 arXiv composition。

## What Changes

- default signals config 改为 5 News + 1 GitHub + 1 Paper，WeChat 在 News 中 optional、最多 2 条。
- 新增 `wechat_max_items` cap；`wechat_min_items` 保留为向后兼容的 explicit minimum，default 改为 0。
- optional WeChat failure 继续显示在 source coverage，但当另一个 viable News source 完成时，不单独降低 briefing outcome。
- optional exception 只适用于 quota mode 且 `wechat_min_items=0` 的 WeChat；HN/X、legacy mode 与 positive WeChat minimum 的 attempted failure 继续影响 outcome。
- personal config、example、Skill、文档与现有 Codex automation prompt 同步新 composition。

## Alternatives Considered

1. **只把 `wechat_min_items` 改为 0** — 能取消 shortfall，但无法保证微信最多两条，且 automation/source failure 仍会使结果 `partial`。
2. **禁用 WeChat source** — 最简单，但失去偶尔可用的微信新内容，不符合“可选 2 条”。
3. **minimum=0 + maximum=2（当前选择）** — 明确区分 required quota 与 optional mix，并保留 legacy minimum compatibility。

## Capabilities Affected

### Modified Capabilities

- `briefing`: default quota、config validation、outcome 与 Markdown quota display。
- `signal-discovery`: News selection 的 optional WeChat cap 与 optional source failure 语义。
- `daily-discovery`: Agent output composition 与 Codex automation prompt。

## Impact

影响 `briefing/signals.py`、`research/discovery/config.py`、`research/discovery/runner.py`、config example、daily Skill、相关 tests/Specs/docs，以及 Codex automation `ai`。不改变 direct WeChat article archive，也不删除现有 local artifact。

## Review Feedback

- [x] 2026-08-15 sdd-reviewer: 明确 attempted-source outcome matrix、补 empty/cap/selective-run anti-overfit case，并要求 automation read-back → 状态: resolved in plan documents
- [x] 2026-08-15 sdd-reviewer verify: explicit zero migration defect 与 optional maximum source-validation assertion 缺口 → 状态: fixed and regression-tested

## Known Gaps

- [ ] WeChat realtime provider 仍使用 best-effort public index；替换为 login-backed feed 属于后续独立 change。
