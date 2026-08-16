# 模块合约与耦合地图

> 这个仓库当前按业务层组织成 `research/`、`collect/`、`library/`、`briefing/`、`publish/` 五层。重点看：统一入口在哪，业务逻辑在哪，输出落到哪。

## 模块概览

| 模块 | 路径 | 对外暴露 | 状态 |
|------|------|----------|------|
| Research Operations | `research/` | `main()`、`collect/query/briefing/backfill/discover/status/schedule` 子命令 | 🟢 active |
| Collect | `collect/` | standalone GitHub/Papers/WeChat + discovery-only HN/X/WeChat index adapter | 🟢 active |
| Library | `library/` | `ResearchItem`、backfill、sidecar 扫描、查询入口 | 🟢 active |
| Briefing | `briefing/` | signal-first daily briefing + legacy digest / reading-list | 🟢 active |
| Publish | `publish/` | Obsidian 友好路径和写文件辅助 | 🟢 active |
| Archive Output | `output/` | 原始抓取归档 + `output/briefing/` 派生阅读产物 | 🟢 stable |
| AI Context | `.compass/context/` + `AGENTS.md` + `CLAUDE.md` | 导航、规则、spec、workflow 说明 | 🟡 active |

## 模块公开 API 清单

### Research Operations

```
main()                                              ✅ STABLE
collect_github_targets()                            ✅ STABLE
collect_paper_categories()                          ✅ STABLE
collect_wechat_article()                            ✅ STABLE
run_discovery() / read_discovery_status()           ✅ STABLE
generate_briefing()                                 ✅ STABLE
run_backfill()                                      ✅ STABLE
```

### Collect

```
# GitHub
main() / save_repo() / repo_to_markdown()          ✅ STABLE

# Papers
main() / fetch_papers_by_category() / save_papers() ✅ STABLE

# WeChat
main() / fetch_article() / normalize_wechat_url()   ✅ STABLE

# Discovery-only realtime adapters
collect_hackernews_feed() / collect_x_query()       ✅ STABLE
discover_wechat_account()                           ✅ BEST-EFFORT
```

### Library

```
ResearchItem                                        ✅ STABLE DATA CONTRACT
discovered_at / signal_role / discovery_method      ✅ STABLE OPTIONAL FIELDS
backfill_output_tree()                              ✅ STABLE
load_research_items()                               ✅ STABLE
query_research_items()                              ✅ STABLE
```

### Briefing / Publish

```
write_digest_report()                               ✅ STABLE
write_reading_list_report()                         ✅ STABLE
write_daily_signal_briefing()                       ✅ STABLE
briefing/main.py main()                             ✅ STABLE
briefing_output_path() / write_markdown()           🔧 INTERNAL SUPPORT
```

## 依赖拓扑

```
research/cli.py ───────────────────────→ collect/
research/cli.py ───────────────────────→ library/
research/cli.py ───────────────────────→ briefing/
research/discovery/runner.py ──────────→ collect/ + briefing/signals.py

collect/ ──────────────────────────────→ library/items.py
library/query.py ──────────────────────→ library/storage.py
briefing/ ─────────────────────────────→ library/query.py + publish/obsidian.py
briefing/signals.py ───────────────────→ library/items.py + publish/obsidian.py

collect/github.py ─────────────────────→ gh CLI
collect/papers.py ─────────────────────→ arXiv API / XML
collect/wechat.py ─────────────────────→ Camoufox / httpx / bs4 / markdownify
collect/wechat_index.py ───────────────→ public WeChat index (best effort)
collect/hackernews.py ─────────────────→ Hacker News public API
collect/x.py ──────────────────────────→ X recent-search API (optional credential)

collect/ + briefing/ + publish/ ───────→ output/
```

## 依赖规则

| 来源 → 目标 | 允许？ | 方式 | 违反后果 |
|-------------|--------|------|----------|
| `research/` → `collect/` / `library/` / `briefing/` | ✅ | dispatch 调用 | 这是唯一 operator surface |
| `collect/` → `library/items.py` | ✅ | 统一 sidecar 写入 | 这是共享模型入口 |
| `library/` → 外部网络依赖 | ❌ | — | 会把本地查询重新耦回抓取流程 |
| `briefing/` → `collect/` | ❌ | — | 简报必须消费本地 sidecar，而不是重新抓远端数据 |
| `briefing/signals.py` → realtime network | ❌ | — | freshness / ranking 必须是可复现的 local selection |
| `publish/` → `output/github|papers|wechat|hackernews|x` | ❌ | — | 派生产物必须与 source archive 隔离 |
| 手工修改 `output/` 试图“修复”格式问题 | ❌ | — | 下次重抓或重生会覆盖，根因没修掉 |

## 变更联动表

| 当你改了… | 必须同步改… | 原因 |
|-----------|-------------|------|
| `research/cli.py` 的子命令或参数 | overview、cli-runtime、README、AGENTS、CLAUDE、traceability | 这是唯一对外命令表面 |
| `collect/wechat.py` 的输出目录或 Markdown 模板 | `tests/test_wechat_collect.py`、`.compass/context` 文档 | 真实实现已直接暴露给统一入口 |
| `collect/github.py` 的 repo / search 输出命名 | `output/github/` 样例、`.compass/context` 文档 | 目录命名和搜索 sidecar 约定会影响查询层 |
| `collect/papers.py` 的类别白名单 | L3 spec、L5 traceability | 类别既是用户入口也是领域约束 |
| `library/items.py` 的 schema 字段 | builders / parsers / `tests/test_research_item.py` / traceability | 会影响所有来源 sidecar 和 briefing 输入 |
| `briefing/signals.py` 的 freshness / rank / status | signal-discovery Spec、daily Skill、Web outcome、fixture tests | 会改变“今天值得看”的产品语义 |
| `collect/hackernews.py|x.py|wechat_index.py` | discovery config、coverage status、source fixture tests | realtime source failure 不得被误报为空结果 |
| `library/query.py` 的过滤规则 | `briefing/` 输出、`tests/test_restructure_research_architecture.py` | briefing 直接依赖查询结果 |
| `publish/obsidian.py` 的输出树 | `features/archive-output/README.md`、overview、traceability | 会改变派生产物边界 |

## 共享代码与跨模块约定

| 共享代码 | 路径 | 使用规则 |
|----------|------|----------|
| 统一内容模型 | `library/items.py` | 所有来源 sidecar 都要走同一 schema，不允许来源各写各的 JSON 结构 |
| 历史 backfill | `research/cli.py` + `library/items.py` | 优先复用既有 Markdown，不要为了查询层重新抓一遍 |
| 本地查询 | `library/storage.py` / `library/query.py` | 输入必须是 sidecar，而不是远端 API |
| 派生阅读产物 | `briefing/` + `publish/` | 只写 `output/briefing/`，不覆盖原始归档 |
| daily signal contract | `briefing/signals.py` + `research/discovery/runner.py` | 按 `source` 分组定额；GitHub destination 不再单独 cap；fresh GitHub/Papers evidence 填 dedicated section；quota/status 区分 shortfall、完整空结果与 coverage failure |
| wechat 自动化测试 | `tests/test_wechat_collect.py` / `tests/test_wechat_e2e_live.py` | 现已迁入根级测试面，和统一入口保持一致 |
