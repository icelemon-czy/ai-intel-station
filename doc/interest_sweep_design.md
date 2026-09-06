# Interest Sweep

Interest Sweep 是 Agent-first 的一次性 topic 拉取。project Agent 把一句“我对 X 感兴趣，把相关内容拉下来”解释为 topic-string `research seek`，runtime 按该 topic 对少数 remote source 做一次 keyword sweep，把命中的 material 收集为本地 archive 并生成这份 reading list。它不是每日 `discover`，也不是只读的本地 `query`。

```text
topic string
    ↓
--dry-run plan → per-source keyword sweep → archive + sidecar
                                                ↓
                                  this-run reading list → output/briefing/reading-lists/
```

## Source 范围

v1 只做 topic keyword sweep，覆盖能按关键词检索或过滤的 source：

| Source | topic 查询方式 | 说明 |
|:-------|:---------------|:-----|
| GitHub | repository search（`gh search repos`） | 复用 `collect/github.py` 的 repo search 能力，不做 code search |
| arXiv | keyword query | 在 `collect/papers.py` category 之外增加 keyword fetch |
| Hacker News | 现有 Firebase feed + keyword 过滤 | 扫描 `newstories` + `showstories`（`collect/hackernews.py`），按 title、url 与 story text 关键词过滤，不用 Algolia |

默认每个 source 拉取上限为 10（`--limit`）。

WeChat 与 X 不在 v1：WeChat 依赖 watchlist / 单篇 URL、X 需要 bearer token，都不是稳定的 topic-keyword 拉取入口。需要它们时走 Daily Discovery 的 source lane 或 standalone collect。

## Observable behavior

- `research seek "<topic>"` 接受一个 topic string，对 v1 source 各做一次 keyword sweep，把命中 item 写入 `output/<source>/` archive 与 `ResearchItem` sidecar。
- `--dry-run` 只列出计划要查询的 source 与 keyword，不联网、不写入任何文件。
- 每个 source 独立报告 success、skip 和 failure；一个 source 失败不影响其他 source 已保存的 artifact。
- persist 前按 `canonical_url` 判重：已存在于本地 Library 的 URL 会被 skip，不重复收集。
- 默认在本次 run 结束后，由 CLI 从本次 sweep 命中的 item 生成一份 this-run reading list，写入 `output/briefing/reading-lists/`；这份清单包含本次新收集的 item，也包含本次命中但本地已存在（因判重被 skip）的 item。
- `--no-briefing` 只收集、不生成 reading list。
- topic sweep 是一次性动作，不写入 run log、不维护 freshness window、不施加 discovery quota。

## Boundary

Interest Sweep 复用 collect 的 source adapter 与 briefing 的 reading-list 产物：`collect/seek.py` 只编排 per-source keyword sweep 与 persist，this-run reading list 由 CLI 经 `briefing.service` 组合；不新增独立 layer 或 state。

| 入口 | 目的 | 输入 | 是否联网 | 产物 |
|:-----|:-----|:-----|:---------|:-----|
| `research seek` | 按 topic 一次性拉取相关内容 | topic string | 是 | archive + sidecar + this-run reading list |
| `research query` | 本地检索已有 Library | keyword / source / 日期 | 否 | 只读结果 |
| `research collect` | 单个 source 的一次性抓取 | repo / category / URL | 是 | 单 source archive + sidecar |
| `research discover` | 每日 signal sweep | `config/discovery.yaml` | 是 | 多 lane archive + signal briefing |

与 `query` 的区别：seek 会真正访问 remote source 并持久化，query 只读本地 sidecar。
与 `collect` 的区别：collect 针对单一 source 与明确 target（repo、category、URL），seek 以一个 topic 编排多个 keyword-capable source。
与 `discover` 的区别：discover 是配置驱动、按 freshness 与 quota 挑选每日 signal 的循环；seek 是无配置、无调度的临时主题拉取。

## CLI 示例

```bash
uv run research seek "agent harness" --dry-run
uv run research seek "retrieval augmented generation"
uv run research seek "vector database" --no-briefing
```

`--dry-run` 用于先看计划；确认后再执行真实 sweep。

## Non-goals

- 不做每日 discovery、schedule 或 coverage/quota 计算，那些属于 Daily Discovery。
- 不新建 `seek` runtime layer，也不引入 `.state/seek/` run log 或持久状态。
- 不提供 Web page；结果通过 reading list 与 conversation 返回。
- 不自动编辑 `config/discovery.yaml`；长期跟踪某主题应显式走 Daily Discovery 的 preferences。
- v1 不覆盖 WeChat、X 或其他需要专用凭据 / watchlist 的 source。

## 入口与 evidence

- Agent surface：`.agents/skills/interest-sweep/SKILL.md`
- Runtime：`src/ai_intel_station/collect/seek.py` 编排 per-source keyword sweep 与 persist（不生成 briefing）；CLI（`src/ai_intel_station/cli/commands.py`）经 `src/ai_intel_station/briefing/service.py` 组合 this-run reading list；`src/ai_intel_station/collect/papers.py` 增加 arXiv keyword fetch；`src/ai_intel_station/collect/hackernews.py` 增加 topic keyword feed scan
- 复用：`src/ai_intel_station/collect/github.py`、`src/ai_intel_station/collect/hackernews.py`、`src/ai_intel_station/briefing/`（reading-list 产物）
- Tests：`tests/test_seek.py`
