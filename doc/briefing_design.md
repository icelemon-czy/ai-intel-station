# Briefing

Briefing 把 local Library 中的 `ResearchItem` 转换成适合 Obsidian 阅读的 Markdown。它不拥有 remote collection；输入已经在本地，输出是可重建的 derived artifact。

## 三类产物

| 类型 | 触发入口 | 用途 |
|:-----|:---------|:-----|
| Digest / Reading List | `research briefing` 或 Web preview/save | 按 keyword、source 和日期过滤本地 Library，生成摘要或待阅读清单 |
| Daily Signal Briefing | `research discover` | 展示 freshness、source lane、confidence、coverage 和 quota 状态 |
| Library Catalog | `research organize` | 提供 date/tag browse 与 duplicate audit，不移动 primary archive |

Digest 与 Reading List 是 generic local-library mode；Daily Signal Briefing 由 Daily Discovery 的 selection contract 驱动；Library Catalog 是从全部 sidecar 重建的 navigation artifact。三类产物共享 output 和 Markdown publishing boundary，但不共享 selection 语义。

## Observable behavior

- generic briefing 只读 sidecar，不触发 source fetch。
- Digest 用普通列表呈现，Reading List 使用 checkbox。
- requested source 没有匹配项时，产物显示 coverage note，而不是伪造完整结果。
- Web preview 只返回 Markdown；只有 Save 才写文件。
- 所有产物写入 `output/briefing/<section>/`，不会覆盖同名旧文件；path collision 使用递增 suffix。
- Library Catalog 固定写入 `output/briefing/library/` 并原位重建，因为它是 current Library 的 index，不是历史 briefing snapshot。
- item 优先链接 canonical URL，并在存在本地 archive 时附 `open local` link。
- title、summary 和 link text 在 Markdown boundary 做必要 escaping，避免 source content 破坏结构。

## 主要 flow

```text
local sidecars → query/filter → select/render → preview
                                      └────→ atomic save → output/briefing/
```

Daily Signal Briefing 在 query 后额外执行 role、freshness、dedupe、ranking、quota 和 coverage 计算；具体 contract 见 [`daily_discovery_design.md`](daily_discovery_design.md)。

## 关键 decision

- Briefing 是 derived reading artifact，不是新的 primary research item。
- preview 与 save 分离，使 Web 用户可以在不写文件时检查结果。
- output path 由 `publish.obsidian` 统一管理，保持 Obsidian-friendly filename 和 atomic write。
- generic mode 保留作为明确的 local Library workflow；Daily Discovery 不用 generic digest 冒充 signal briefing。
- Catalog 只建立 browse view，不根据不完整 metadata 自动移动、retag 或删除 primary material。

## 入口与 evidence

- Runtime：`briefing/service.py`（generic build/save）、`briefing/reports.py`（render）、`briefing/signals.py`、`briefing/signal_rendering.py`、`publish/obsidian.py`
- CLI：`research briefing ...`、`research briefing --list`
- Tests：`tests/test_briefing_reports.py`、`tests/test_briefing_path_and_run_log.py`、`tests/test_obsidian_publish.py`、`tests/test_signal_rendering.py`
