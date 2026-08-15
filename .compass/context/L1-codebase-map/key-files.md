# 通用任务食谱与调查起点

> 这里放跨模块的共用修改套路。来源细节去各自 `features/` 文档看；命令表面一律先从 `research/cli.py` 开始判断。

## 常见任务食谱

### 食谱 1: 调整统一命令表面

**参考已有实现**: `research/cli.py`

```text
步骤：
1. 先确认变化落在 collect / query / briefing / backfill 哪个子命令。
2. 在 `build_parser()` 和对应 dispatch 函数一起改，避免 parser 和执行路径脱节。
3. 如果子命令变化会影响输出或行为说明，同步更新 README、AGENTS、CLAUDE、`.compass/context`。
4. operator surface 的变化优先补 `tests/test_restructure_research_architecture.py`。

验证：`uv run --with pytest python -m pytest tests/test_restructure_research_architecture.py`
```

### 食谱 2: 调整某个 collect 来源

**参考已有实现**: `collect/github.py`、`collect/papers.py`、`collect/wechat.py`；daily realtime adapter 看 `collect/hackernews.py`、`collect/x.py`、`collect/wechat_index.py`

```text
步骤：
1. 先确认真实实现是不是在 `collect/<source>.py`，不要回到历史来源目录找入口。
2. 把“拉取数据 → 转 Markdown → 落盘 → sidecar”保持成单条清晰管线。
3. 如果改动影响输出结构或 Markdown 字段，同步更新 output 说明和 `.compass/context`。
4. WeChat 的纯转换变化优先补 `tests/test_wechat_collect.py`。
5. Realtime adapter 必须使用 local fixture 覆盖 success、remote/malformed failure 与 bounded request；不得用 live response 代替回归测试。

验证：重跑对应单测或最小 collect 命令，确认 `output/<source>/` 结构不漂移。
```

### 食谱 3: 调整统一内容模型或 sidecar/backfill

**参考已有实现**: `library/items.py`

```text
步骤：
1. 先确认 schema 变化是否影响 builder、parser、backfill 三条路径。
2. 优先保持历史 Markdown 可复用，不要为了新字段要求重新抓取。
3. 若 sidecar 命名或字段变化，必须同步 query、briefing 和 traceability。

验证：`uv run --with pytest python -m pytest tests/test_research_item.py`
```

### 食谱 4: 调整查询或 briefing

**参考已有实现**: `library/query.py`、`briefing/reports.py`、`briefing/signals.py`、`publish/obsidian.py`

```text
步骤：
1. 查询层只能消费本地 sidecar，不要回 collect 层重新抓远端数据。
2. daily News item 必须来自 verified fresh `signal`；GitHub / Papers 保持 evidence role，
   只 MAY 进入各自 dedicated lane 或 corroborate，不能填 News。
3. briefing 只能写 `output/briefing/`，不要覆盖原始归档。
4. 部分成功必须继续保留，并显式写出缺失来源；零 item 时区分 `no_fresh_signals` 与 `coverage_incomplete`。

验证：`uv run --with pytest python -m pytest tests/test_restructure_research_architecture.py`
```

## 通用变更影响

| 当你改了这个文件 | 影响范围 | 必须做的事 |
|-----------------|----------|-----------|
| `research/cli.py` | 统一 operator surface、命令语义、根级运行方式 | 跑 `tests/test_restructure_research_architecture.py`，同步 README / AGENTS / CLAUDE / `.compass/context` |
| `collect/wechat.py` | 微信抓取行为、Markdown 模板、图片下载 | 跑 `tests/test_wechat_collect.py`，必要时确认 `tests/test_wechat_e2e_live.py` 的 skip/live 行为 |
| `collect/github.py` | GitHub 抓取命令、输出结构、`gh` 依赖边界 | 至少做一次命令级 smoke 或补更强测试计划，核对 `output/github/` |
| `collect/papers.py` | 分类白名单、论文命名、摘要模板 | 至少做一次命令级 smoke 或补更强测试计划，核对 `output/papers/` |
| `library/items.py` | 统一 schema、sidecar、backfill 行为 | 跑 `tests/test_research_item.py` |
| `library/query.py` / `briefing/reports.py` / `publish/obsidian.py` | 查询结果、briefing 内容、派生输出路径 | 跑 `tests/test_restructure_research_architecture.py` |
| `briefing/signals.py` / `research/discovery/runner.py` | freshness、rank、coverage 与 daily outcome | 跑 `tests/test_realtime_signals.py`、runner suite 与 Web outcome tests |
| `pyproject.toml` | 根级打包、`research` script、pytest 配置 | 确认根级测试仍从 workspace 根可执行 |

## 调查起点

| 问题类型 | 从这里开始查 | 排查思路 |
|----------|-------------|----------|
| `research` 子命令行为不对 | `research/cli.py` | 先确认 parser、dispatch、默认参数是否一致 |
| 微信 URL 粘贴后报错 | `normalize_wechat_url()` → `tests/test_wechat_collect.py` | 先看是不是转义字符、HTML entity 或缺 scheme |
| 微信输出缺图 / 图片地址不对 | `download_all_images()` → `replace_image_urls()` | 先分清是下载失败还是 Markdown 重写失败 |
| GitHub collect 失败 | `run_gh()` | 失败信息来自 `gh` stderr，先验证本地 `gh` 是否可用 |
| papers 某个类别没输出 | `AI_CATEGORIES` → `fetch_papers_by_category()` | 先看类别是否合法，再看 API 返回是否为空 |
| 本地查询结果不对 | `load_research_items()` → `query_research_items()` | 先确认 sidecar 是否存在，再确认过滤条件是否过严 |
| daily briefing 缺来源或排序异常 | `select_daily_signals()` → `write_daily_signal_briefing()` | 先查 role / publication time / coverage，再查 deterministic ranking；不要用旧 evidence 填榜 |
| 生成内容和文档不一致 | README / SKILL / `.compass/context` 文档 | 这类问题常常不是代码错，而是命令或路径说明未同步 |

---

> 新增来源、修改输出约定、或调整 operator surface 后，先回这里补食谱，再补 feature 文档。
