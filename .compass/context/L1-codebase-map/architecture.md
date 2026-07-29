# 运行时架构

> 这个仓库不是常驻服务。primary interaction 是 project Agent + Skill，Agent 调用统一
> `research` CLI；deterministic runtime 仍按 `research/` → `collect/` → `library/`
> → `briefing/` → `publish/` 运行。Web 只是 optional viewer。

## 部署拓扑

```
Project Agent / 本地 Shell
  ├─ .agents/skills/daily-discovery/
  │    └─ intent → setup / today / preferences / status / schedule
  │
  ├─ research/cli.py
  │    ├─ collect github / papers / wechat
  │    ├─ query
  │    ├─ briefing
  │    └─ backfill
  │
  ├─ collect/
  │    ├─ github.py   → gh CLI / GitHub 数据
  │    ├─ papers.py   → arXiv API / XML
  │    └─ wechat.py   → Camoufox / httpx / BeautifulSoup / markdownify
  │
  ├─ library/
  │    ├─ items.py    → 统一 ResearchItem schema / parse / backfill
  │    ├─ storage.py  → 扫描既有 sidecar
  │    └─ query.py    → 关键词 / 来源 / 时间过滤
  │
  ├─ briefing/
  │    ├─ reports.py  → digest / reading list Markdown
  │    └─ main.py     → 本地简报 CLI
  │
  └─ publish/
       └─ obsidian.py → output/briefing/* 路径与写文件辅助
```

## 主要执行生命周期

### 收集命令

```
research collect <source> ...
  → research/cli.py dispatch
  → 外部依赖调用（gh / arXiv / Camoufox）
  → Markdown 组装
  → library.items 写 ResearchItem sidecar
  → output/<source>/... 原始归档
```

### 历史 backfill 命令

```
research backfill output
  → research/cli.py
  → library.items.backfill_output_tree()
  → 解析既有 Markdown / search.md
  → 生成 research-item.json / research-items.jsonl
  → 不改原始 Markdown，只补 sidecar
```

### 本地简报命令

```
research briefing <mode> <keyword>
  → research/cli.py
  → library.storage.load_research_items()
  → library.query.query_research_items()
  → briefing.reports.build_*_markdown()
  → publish.obsidian.write_markdown()
  → output/briefing/digests/ or reading-lists/
```

## 运行时协作关系

| 层 | 责任 | 调用方式 | 说明 |
|----|------|----------|------|
| `research/` 入口层 | 统一 collect / query / briefing / backfill 命令表面 | 根级 script / `python -m research` | 对外只暴露这一层 |
| `collect/` | 外部数据采集与原始 Markdown 落盘 | CLI 同步触发 | 对外部依赖最敏感 |
| `library/` | 统一模型、历史 sidecar 扫描、本地查询 | 纯 Python 函数 | 不要求重新抓取就能工作 |
| `briefing/` | digest / reading list 组装 | 本地 CLI 或函数调用 | 允许部分成功，但要标缺口 |
| `publish/` | 派生输出写入 `output/briefing/` | 文件系统写入 | 不应回写原始抓取目录 |

## 启动与初始化顺序

### 收集链路

```
1. 解析 CLI 参数
2. `research/cli.py` dispatch 到 collect 层
3. 校验参数 / 模式
4. 调外部依赖
5. 组装 Markdown + sidecar
6. 写入 output/<source>/
```

### 查询 / 简报链路

```
1. 解析 CLI 参数
2. 扫描 output/ 下现有 sidecar
3. 执行关键词 / 来源 / 时间过滤
4. 生成 digest 或 reading list
5. 写入 output/briefing/
```

## 执行边界与拦截点

1. **参数预处理**：URL 归一化、类别白名单、owner/repo 格式、briefing mode 选择
2. **外部依赖边界**：Camoufox、`gh`、arXiv API；只允许出现在 `collect/`
3. **资料边界**：`library/storage.py` 只消费 sidecar，不直接重新抓远端数据
4. **输出边界**：原始抓取产物只能写 `output/wechat|github|papers`，派生阅读产物只能写 `output/briefing`

## 错误传播路径

```
collect/wechat.py
  抓取 / 下载异常
    → fetch_article() 抛出
    → CLI main() 打印失败并退出

collect/github.py
  gh 返回非 0
    → run_gh() raise RuntimeError
    → 当前命令失败

collect/papers.py
  单个 category 失败
    → 打印 warning
    → 继续下一个 category

briefing/main.py
  sidecar 不存在或查询为空
    → 仍可生成简报，内容可能为空或仅带 coverage note
```

## 关键运行时配置

| 配置项 | 来源 | 影响 | 默认值 |
|--------|------|------|--------|
| `OUTPUT_DIR` / `DEFAULT_OUTPUT_DIR` | `collect/*` 常量 | 决定原始归档落盘位置 | `output/wechat` / `output/github` / `output/papers` |
| `DEFAULT_OUTPUT_ROOT` | `research/cli.py` 常量 | 决定统一入口默认输出根目录 | `output` |
| `IMAGE_CONCURRENCY` | `collect/wechat.py` 常量 | 图片下载并发度 | `5` |
| `WECHAT_E2E_URLS` | 环境变量 | 是否运行微信 live e2e | 空值时跳过 |
| `gh` 登录状态 | 本地 CLI 环境 | GitHub 工具能否成功拉取数据 | 必须可用 |
