# Roadmap — Restructure Research Architecture

## North Star

把当前“分来源抓取 Markdown”的仓库，逐步改成一条更完整的业务链：先收集资料，再整理进资料库，再按主题和条件出简报，最后把结果交付给 Obsidian 阅读。

## Current State

- GitHub / papers / wechat 仍然主要以各自脚本为边界组织代码
- `ResearchItem` 已经落地，但目前更多承担统一 sidecar 与 backfill 的职责
- `output/` 适合做原始归档，不适合直接承载未来的查询和简报逻辑
- Obsidian 适合看结果，不适合当主交互入口

## Target Architecture Overview

```text
collect/
  github/
  papers/
  wechat/

library/
  items/
  storage/
  time/
  query/
  ranking/
  topics/

briefing/
  backfill/
  query/
  reports/

publish/
  obsidian/
  cli/
```

对应业务含义：

- `collect/`：按来源收集资料
- `library/`：统一入库、整理、查询、排序
- `briefing/`：生成周报、专题页、阅读清单
- `publish/`：把结果交付给 Obsidian 或命令行

## Structure Principles

1. `collect/` 只负责按来源收集资料，不承载查询、筛选和出简报逻辑。
2. `ResearchItem`、查询、时间过滤、排序等能力都放在 `library/`，不再继续散落在来源脚本里。
3. 现有 CLI 先保留，内部逐步改成调用新结构，避免用户命令失效。
4. `output/<source>/` 继续保存原始归档；给 Obsidian 看的周报、专题页、阅读清单要单独组织。
5. 时间是一个可选过滤条件，不应该变成必须输入项。
6. 这一阶段先不引入 Web/TUI，重点先把“可查、可筛、可出简报”做出来。

## Suggested Migration Shape

### Phase 0 — Foundation Already Started

- 保留并巩固 `ResearchItem` 作为跨来源统一对象
- 保持现有抓取 CLI 和原始 Markdown 输出兼容
- 确保历史 backfill 能持续工作

Exit criteria:

- `ResearchItem` 仍是跨来源最小公共模型
- 原始 source-specific sidecar 约定稳定

### Phase 1 — Code Structure Reshape

- 把当前共享逻辑从仓库根和各抓取脚本中抽到 `library/`
- 为 GitHub / papers / wechat 建立明确的 `collect/` 边界
- 让现有 `fetch_*.py` 退化成薄壳入口

Exit criteria:

- 核心逻辑不再散落在 3 个抓取脚本中
- CLI 兼容保持不变
- `.ai` 导航能清楚区分 `collect/`、`library/`、`briefing/`、`publish/` 四层

### Phase 2 — Local Query And Report Layer

- 引入基于 `ResearchItem` sidecar 的本地查询入口
- 支持来源、时间、标签、关键词等基础过滤，其中时间是可选条件
- 生成 Obsidian 可直接阅读的周报、专题页、阅读清单 Markdown

Exit criteria:

- 可以不重新抓取、直接基于本地归档生成主题报告
- Obsidian 中看到的内容不只是原始抓取结果，而是经过组织后的阅读产物

### Phase 3 — High-Signal Filtering

- 增加 ranking、quality scoring、去重和主题聚类
- 区分“原始抓取结果”与“值得读的结果”
- 为后续用户使用提供更高信号的候选集合

Exit criteria:

- 能稳定产出“最近最值得读”或“某主题高质量候选”
- 同主题多来源内容能被聚合而不是简单并列

### Phase 4 — Interaction Layer Outside Obsidian

- 这部分不放进当前 change，只作为后续方向保留
- 如果以后要做，优先从 CLI 开始，再看是否需要 Web/TUI
- Obsidian 仍然只消费产物，不承担主要交互状态管理

Exit criteria:

- 用户能通过非 Obsidian 入口发起查询、筛选和报告生成
- 交互结果可以回写为 Obsidian Markdown 页面

## Near-Term Priorities

1. 先确认 Phase 1 的结构边界和兼容性要求
2. 再把 Phase 2 的 query / report 作为第一批新增能力写入 delta spec
3. ranking / dedup / clustering 放在 query/report 基础稳定之后
4. Web/TUI 不进入当前 change 范围

## Risks To Control

- 过早把 Obsidian 当成交互壳层，会把核心能力绑死在特定 UI 上
- 过早做 Web/TUI，可能在核心 query/report 还不稳定时放大复杂度
- 一次性迁移全部抓取脚本，会增加兼容和验证成本
- 如果不保留 source-specific 原始归档，后续回放和审计会变差

## Proposal Dependency

本 roadmap 依赖 `add-research-item` 作为基础变更。只有统一对象、sidecar 和 backfill 稳住之后，后续结构重组和 query/report 才有稳定输入。
