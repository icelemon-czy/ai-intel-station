# Classify Briefing By Source

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

- `2026-08-15 23:55` — [无] → drafting by /develop | 原因: 用户确认按 source 分组与定额，撤销 GitHub destination cap
- `2026-08-15 23:58` — drafting → implementing by /develop | 原因: plan review PASS；按 source 定额、忽略 destination cap、news_items 迁移为 hackernews_items、ownership 顺序无 blocker
- `2026-08-16 00:16` — implementing → pending-review by /develop | 原因: 相关测试绿灯；`pytest tests/test_realtime_signals.py tests/test_discovery_config.py tests/test_agent_first_runtime.py tests/test_restructure_research_architecture.py tests/test_briefing_marker.py` 110 passed / 4 subtests；`unittest tests.test_discovery_runner` 15 passed
- `2026-08-16 00:17` — pending-review → approved by /develop | 原因: Main Agent verify PASS；selector/renderer/config/Skill 与 merged Spec 对齐；destination cap 已删除；无未解决业务歧义
- `2026-08-16 00:18` — approved → archived by /develop | 原因: delta 已合并进 briefing / signal-discovery / daily-discovery / github / papers 主 Spec；L1/L2/L5 已同步

## Why

Daily briefing 用 `news` lane 把 HN / WeChat / X 混成一桶，再用 URL hostname 限制
GitHub destination。这在 briefing 层发明了 collect/library 没有的内容分类轴，也让
HN 上的 repo 发布看起来像 GitHub 资讯。用户要的是按已有 `source` 分类展示和定额。

## What Changes

- **BREAKING** quota-mode daily artifact 按 source 分组：`arXiv` / `GitHub` /
  `Hacker News` / `WeChat` / `X`。`news` 不再是用户可见 lane。
- **BREAKING** 新/default quota 使用独立 source 定额：`hackernews_items=3`（required
  when positive）、`wechat_min_items=0`、`wechat_max_items=2`（optional）、
  `x_items=0`、`github_items=1`、`paper_items=1`。WeChat 空缺不再把 HN 补到 5 条。
- 删除 `github_news_max_items` 与 destination-host 分类。HN story 指向 github.com
  仍归 Hacker News。GitHub collector evidence 仍只进 GitHub section。
- 跨 source exact URL/title 仍只展示一次；ownership 为
  `papers > github > hackernews > wechat > x`。被拥有的 realtime signal 作为
  corroboration，不占被拥有 source 以外的定额。
- existing quota YAML 有 `news_items` 但没有 `hackernews_items` 时，迁移为
  `hackernews_items = news_items`（保留原 HN 容量；WeChat 改为独立 optional quota，
  总数可能略增）。新 example / 缺省字段使用 `hackernews_items=3`。现有
  `github_news_max_items` 忽略且不影响 selection。
- `news_items` 与 `max_items` 混用仍是 config error；`hackernews_items` /
  `x_items` 加入同一 quota-field 集合。
- Daily Skill 按 source 返回，报告各 required source expected / actual / missing，
  以及 WeChat optional maximum；不再报告 GitHub destination excluded count。
- HN title 仍链接 canonical target，`hackernews` attribution 仍优先
  `discussion_url`。normalized URL 只用于 identity，不再做 host classification。
- legacy `max_items` 模式保持混合 realtime cap，不启用 per-source quota。

## Alternatives Considered

1. **只改展示、保留混合 News 选择** — 分组好看，但 HN 仍可能占满实时名额，destination
   cap 的根因还在。
2. **保留 News 桶 + 按 source 定额填这个桶** — 用户仍看到 News 概念，和 `source`
   分层不一致。
3. **按 source 展示且按 source 定额（当前选择）** — 使用 collect 已写入的 `source`，
   删除 destination 分类器，`news` 降为内部实现细节。

## Capabilities Affected

### Modified Capabilities

- `briefing`: daily artifact 按 source 分组与定额；删除 destination cap 合同。
- `signal-discovery`: 删除 GitHub destination cap；realtime 选择改 per-source。
- `daily-discovery`: Skill 与 init-config 默认 composition 改为 source groups。
- `github`: evidence 不得填充 realtime source quota（原 News slot 措辞）。
- `papers`: evidence 不得填充 realtime source quota（原 News slot 措辞）。

## Impact

- `briefing/signals.py` selector / renderer / `DailyBriefingSelection`
- `research/discovery/config.py` quota parse、migration、required-source validation
- `research/discovery/runner.py` dry-run composition 与 briefing 参数
- `config/discovery.yaml.example`、README、daily Skill、L1/L2
- `tests/test_realtime_signals.py`、`tests/test_discovery_config.py`、
  `tests/test_agent_first_runtime.py`

## Review Feedback

## Known Gaps

- Codex 本机 automation prompt 若仍写 “5 News”，不在本仓库内；归档后如仍存在需另改。
