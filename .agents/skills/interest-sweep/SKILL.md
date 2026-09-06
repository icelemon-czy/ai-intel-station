---
name: interest-sweep
description: "Pull content for a one-off topic string with `research seek`: keyword-sweep GitHub, arXiv and Hacker News, persist new hits into the local archive and return a this-run reading list. Use for 我对 X 感兴趣、把相关内容拉下来、按主题抓取、topic pull/seek；do not use for the daily signal loop (use daily-discovery), a single repo/paper/WeChat URL fetch (use the source playbooks), a local-only query, or product code changes."
---

# Interest Sweep — Agent-first 一次性 topic 拉取

把“我对 X 感兴趣，把相关内容拉下来”转成一次 `research seek`，并把本次收集结果带回
conversation。用户不需要记 CLI 参数或 reading-list 路径。

```text
用户给出 topic
  → 只想要计划时先 `research seek "<topic>" --dry-run`
  → 用户要真正拉取时执行 `research seek "<topic>"`
  → 读取 per-source 结果与 this-run reading list
  → 返回命中重点、skip/failure 与 reading list 本地路径
```

## Boundary

- 复用 `research seek` runtime；不要在 Skill 中重新实现 collect、query 或 briefing。
- 允许真实 run 写入 `output/<source>/` archive、sidecar 与 `output/briefing/reading-lists/`。
- 用户只是想“看看会拉哪些内容 / 先给个计划”时，只跑 `--dry-run`，不联网、不写入。
- 不启动 Web；Web 是 optional viewer，不是完成本 Workflow 的前置条件。
- 不编辑 `config/discovery.yaml`；seek 是一次性动作，长期跟踪某主题才走 Daily Discovery 的 Preferences。
- 不新建 state、不添加每日调度，也不把 seek 扩张成 daily sweep。

## Intent routing

| 用户 intent | Action |
|:------------|:-------|
| “我对 X 感兴趣 / 把 X 相关内容拉下来 / 按主题抓一批” | Seek |
| “先看看会拉到什么 / 别急着下载” | Seek + `--dry-run` |
| “只要收集，不要清单” | Seek + `--no-briefing` |
| “今天有什么值得看 / 每日情报” | 转 daily-discovery Skill |
| “只抓这个 repo / paper category / 微信 URL” | 转 `.agents/playbooks/github\|papers\|wechat/` |
| “本地已有的资料里搜 X” | 用 `research query`，不是 seek |

## Flow

### 1. Confirm scope

1. 在 repository root 工作；确认用户给出的是一个 topic string，而不是单个 repo、paper
   category 或 WeChat URL（后者交给 source playbook）。
2. topic 太宽或含糊时，只问一个澄清问题把它收敛成可检索的关键词，不自行扩大范围。

### 2. Plan first when unsure

用户只想要计划、或不确定会拉到什么时，先执行只读 dry-run：

```bash
uv run research seek "<topic>" --dry-run
```

报告将查询的 source 与 keyword，不联网、不写入。用户确认后再进入 Seek。

### 3. Seek

```bash
uv run research seek "<topic>"
```

- 从 command output 读取每个 source 的 success / skip / failure。
- 已存在的 `canonical_url` 会被 skip，不重复收集——把它解释为“本地已有”，不是失败。
- 默认已生成 this-run reading list；用户显式说“不要清单”时改用
  `uv run research seek "<topic>" --no-briefing`。

### 4. Handoff

- “今天有什么值得看 / 每日 / 自动探索” → 交给 `daily-discovery` Skill，不当成一次性 seek。
- 单个 repo、paper category 或 WeChat 文章 URL → 交给 `.agents/playbooks/` 下对应 source
  playbook，那是 one-off 单 source fetch，不是 topic sweep。

## Output

优先返回用户价值，不返回 command transcript：

- 本次按 topic 命中的重点（按 GitHub / arXiv / Hacker News 分组）
- 每个 source 的 succeeded / skipped（已存在）/ failed
- this-run reading list 的本地路径
- 需要用户决策的唯一 blocker（如果存在，例如某个 source 因凭据或网络不可用）

## Trigger checks

Positive:

- “我对 agent harness 感兴趣，把相关内容拉下来。”
- “按 retrieval augmented generation 抓一批论文和仓库看看。”
- “先别下载，告诉我 vector database 会拉到些什么。” → dry-run

Negative:

- “今天 AI 圈有什么值得看？” → Daily Discovery
- “只抓取这个微信公众号 URL。” → one-off WeChat playbook
- “在本地库里搜 vector database。” → `research query`
- “实现一个 arXiv keyword collector。” → product development

## Anti-patterns

- 在 Skill 中解析远端 API、生成 sidecar 或复制 Python business logic。
- 把一次性 seek 写成每日任务或去改 `config/discovery.yaml`。
- 用户只要计划时却执行了真实联网 run。
- 为展示结果启动 Web server，或把单个 repo/paper/URL 请求当成 topic sweep。
