# Research Library

Research Library 把不同来源的内容保存为 source-segregated Markdown archive，并用统一的 `ResearchItem` sidecar 提供本地查询。它让收集和阅读解耦：remote fetch 只发生在 collect/discovery，query、briefing 和 Web Library 只读本地数据。

```text
GitHub / arXiv / WeChat / realtime sources
                    ↓ collect
         output/<source>/*.md
                    +
          ResearchItem sidecar
                    ↓
      query / briefing / Web Library
```

## Observable behavior

- `research collect` 支持 standalone GitHub repository/search、arXiv category 和单篇 WeChat article。
- 每个 source 写入自己的 `output/<source>/`；原始 Markdown 不写入 `output/briefing/`。
- collector 同步写入 `research-item.json`、`*.research-item.json` 或 `research-items.jsonl` sidecar。
- `research query` 只扫描本地 sidecar，可按 keyword、source、`since` 和 `until` 过滤，不触发 remote fetch。
- `research organize` 从 sidecar 重建 date、tag 和 duplicate catalog，不移动或删除 primary archive。
- `research backfill output` 从历史 Markdown 重建可识别的 sidecar，保留已有 archive 作为 primary material。
- 单个损坏或旧 schema sidecar 会被跳过或兼容读取，不阻断其余 Library。

## Boundary

`ResearchItem` 是 collector、Library、briefing 和 Web workspace 共享的数据 contract。它保存 source、item type、标题、canonical URL、时间、tags、本地 output path，以及 daily discovery 使用的 `signal_role` 和 `discovery_method`。

原始 archive 与派生产物的 ownership 不同：

| Artifact | Ownership | 说明 |
|:---------|:----------|:-----|
| `output/github/`、`papers/`、`wechat/`、`hackernews/`、`x/` | collect / discovery | 原始或 source-normalized research material |
| `ResearchItem` sidecar | Library contract | 跨 source 的结构化索引 |
| `output/briefing/` | briefing | 可重建的 derived reading artifact |

## Organization model

Physical path 与 browse dimension 分离：

- 第一层固定按 source 分区，避免不同 source 的 artifact、metadata 和 update behavior 混在一起。
- 第二层使用不会随分类变化的 stable source identity；batch query、category、feed 和 watchlist 作为 provenance metadata 或 snapshot context，不作为 item 的唯一身份。
- Date 适合 chronological browse 和 freshness filter，不作为 physical ownership；否则同一 item 在更新或跨日期发现时会移动。
- Topic 由显式 tag 表达，不从 title 猜测；当前 GitHub、HN 和 WeChat 的 tag coverage 不足以安全驱动物理目录。
- 相同 canonical URL 可能来自跨 arXiv category 或跨 HN feed，catalog 报告 duplicate context，但不自动删除。

| Source | Target physical identity | Secondary dimension |
|:-------|:-------------------------|:--------------------|
| GitHub repository | `owner/repo` | search query、collection date |
| GitHub search snapshot | normalized query + collection timestamp | result repository identity |
| arXiv | `arxiv-id` | category 合并进 tags/provenance，同一 paper 不按 category 复制 primary material |
| WeChat article | canonical URL identity；date + readable slug 只用于 path display | account、tag；Markdown、sidecar 与 relative image 保持同目录 |
| Hacker News / X | story/post ID | feed、query、rank 与 discovered date |
| Briefing | artifact type + generation date | Library Catalog 使用固定可重建 path |

Physical archive 已按上表迁移：collector 与 discovery writer 直接写 target layout，历史 archive 通过共享的 `library.migration` service（`research migrate archive`）迁移，duplicate copy 只在 canonical identity 与 content equivalence 都可证明时合并并保留 category / feed / query provenance，`output_path` 与 WeChat relative image 保持可解析。

`research organize` 把可重建 index 写入 `output/briefing/library/`：

| Artifact | 用途 |
|:---------|:-----|
| `index.md` | item/source/tag/undated/duplicate/orphan overview |
| `by-date.md` | 依次使用 `published_at`、`updated_at`、`discovered_at` 分组 |
| `by-tag.md` | 按显式 tag 浏览，并列出 untagged item |
| `duplicates.md` | 按 canonical URL 审计重复 context |
| `orphans.md` | 列出没有 sidecar 引用的 Markdown，等待人工 backfill、move 或 deletion decision |

`output/` 是 user-owned local data，Git tracking 只是一种 operator backup choice，不属于 runtime contract。Runtime 不自动 `git add` 或删除 archive；test 必须使用 temporary output root，不能依赖或修改 repository 中的真实 Library。

## 主要 flow

1. source adapter 获取并 normalize source data。
2. collector 写 Markdown archive，并以 atomic write 写 sidecar。
3. `library.storage` 加载全部 sidecar；无效单项只记录 warning。
4. `library.query` 在本地执行过滤和按时间排序。
5. briefing 与 Web workspace 消费查询结果，不绕过 Library 重新抓取。

## 关键 decision

- 使用 sidecar 而不是中央 database，保持 local-first、可检查和易迁移。
- 保留 source-specific archive，避免不同来源的 metadata 和原文语义被过早抹平。
- GitHub repository/search 与 arXiv paper 在 daily discovery 中默认是 `evidence`；它们仍可通过 standalone collect 和 Library 独立使用。
- output path 尽量保存为 repository-relative POSIX path，使 Markdown link 和不同 cwd 下的 runtime 保持稳定。

## 入口与 evidence

常用 standalone operation：

```bash
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
uv run research collect papers cs.AI --max 10
uv run research query agent --source github
uv run research backfill output
uv run research organize
```

direct WeChat article collection 需要先安装 optional browser runtime，再传入 article URL：

```bash
uv sync --extra wechat
uv run research collect wechat "https://mp.weixin.qq.com/s/example"
```

- Runtime：`src/ai_intel_station/cli/commands.py`、`src/ai_intel_station/collect/`、`src/ai_intel_station/library/items.py`（model/write）、`src/ai_intel_station/library/backfill.py`（legacy parser/backfill）、`src/ai_intel_station/library/query.py`、`src/ai_intel_station/library/catalog.py`
- Contract tests：`tests/test_research_item.py`、`tests/test_e2e_archive.py`、`tests/test_cli_e2e.py`、`tests/test_library_query_datetime.py`、`tests/test_library_catalog.py`
