# Clarify Web Workspace Page Purpose Copy

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

- `2026-06-01 00:00` — [无] → [drafting] by /new-change | 原因: 创建 Web workspace 页面目的说明文案 proposal，等待业务确认
- `2026-06-01 14:05` — [drafting] → [implementing] by /continue-change | 原因: 业务确认推进
- `2026-06-01 14:35` — [implementing] → [pending-review] by /continue-change | 原因: 3 个新测试全绿 + 56/56 tests/test_web_workspace.py 绿灯

## Why

当前 Web 工作台已经具备 Dashboard、Library、Briefing Workspace、Collect Workspace 等页面，但页面说明偏短且偏技术，首次使用者不容易理解每个页面负责什么、读取什么数据、完成后会得到什么结果。

本变更先做一个最小试点：在四个 workspace 页面补齐一致的描述性文案，让用户在不阅读 README 的情况下也能判断该从哪个页面开始操作。

## What Changes

- 为 Dashboard 增加页面目的说明：说明它用于查看本地资料库健康度、来源覆盖、最近简报和缺口。
- 为 Library 增加页面目的说明：说明它只搜索本地归档的 ResearchItem / sidecar，不会重新联网抓取。
- 为 Briefing Workspace 增加页面目的说明：说明它基于本地资料生成 digest 或 reading list，并区分 preview 与 save 的产出。
- 为 Collect Workspace 增加页面目的说明：说明它用于手动收集 GitHub、arXiv、WeChat 资料并写入本地输出目录。
- 文案应是短句和工作流提示，不新增 onboarding 向导、弹窗、复杂帮助系统或新的后端数据模型。
- 不改变现有 API、输出路径、采集逻辑、查询逻辑或 briefing 生成逻辑。

## Alternatives Considered

1. **一次性加入完整帮助中心 / glossary** — 能解释更多术语，但会扩大信息架构和交互范围，不适合作为第一步。
2. **只改 README，不改前端** — 对维护者有帮助，但无法解决用户在 Web 工作台内切页时的即时理解问题。
3. **在每个页面加入一致的目的说明（当前选择）** — 改动小、风险低，并且直接覆盖用户当前“不知道这些页面干什么”的问题。

## Capabilities Affected

### New Capabilities

- `research-web-workspace`: 本地 Web 工作台应在 Dashboard、Library、Briefing Workspace、Collect Workspace 页面内展示足够的页面目的、数据来源和产出说明。

### Modified Capabilities

- 无。当前 `.ai/L3-specs/specs/` 中尚无 `research-web-workspace` 主 spec，本变更将先以新能力域 delta spec 记录 Web 工作台的说明性文案要求。

## Impact

- 前端界面：`web/src/App.jsx`、可能涉及 `web/src/styles.css`。
- Web 工作台测试：`tests/test_web_workspace.py` 可增加对关键页面文案的回归断言。
- 不涉及 `output/` 生成产物，不改变 `workspace_web/server.py` API 合约，不新增外部依赖。

## Review Feedback

- [ ] 无

## Known Gaps

- [ ] First-run / empty state 的专项引导不在本变更内，后续单独以 `add-first-run-empty-state-guidance` 处理。
- [ ] Collect source 卡片、Briefing mode 详细解释、Library detail 扩展等更细粒度说明不在本变更内，后续按优先级逐个拆分。
