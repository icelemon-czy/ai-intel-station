# Daily Discovery — Agent-first 每日情报

primary interface 是 project Agent + `daily-discovery` Skill。Agent 负责理解 intent、执行
deterministic CLI、读取 local briefing，并把重点直接返回 conversation；Web 不是前置条件。

## 日常使用

在 project-aware Agent 中直接说：

- “今天有什么值得看？”
- “现在跑每日情报，给我 arXiv、GitHub 和 Hacker News 重点。”
- “把每日搜索主题改成 agent memory。”
- “每天早上九点自动跑。”
- “昨天为什么失败？”

Agent 会检查现有 status，避免重复执行今日成功 run；需要运行时创建或最小修改 ignored
config，执行 dry-run validation，读取 signal briefing / log，并默认返回 3 条 Hacker News +
optional、最多 2 条 WeChat + 1 条 GitHub + 1 条 arXiv，以及 partial failure / quota shortfall。
GitHub / Papers 保持 evidence role，只能进入各自 source section，不会挤占 Hacker News 或 WeChat quota。
只有明确要求 install schedule 时才修改本机 scheduler。

## Lightweight bootstrap

默认环境只安装 core runtime：

```bash
uv sync --frozen
```

这条路径支持 Hacker News、WeChat public-index watchlist、GitHub、Papers、local
query、briefing、discover、status 与 schedule control。X 只需外部 bearer-token env；
WeChat browser stack 只有直接抓全文时才安装：

```bash
uv sync --extra wechat
```

未安装 WeChat extra 时，WeChat command 会返回这条 guidance；不会阻止其他 source 或输出
Python traceback。

## Manual CLI fallback

```bash
# 1. 拷贝示例配置（首次）
uv run research init-config
#   ↳ 在 config/discovery.yaml.example 的基础上写入 config/discovery.yaml

# 2. 试运行（不联网，只看会跑什么）
uv run research discover --dry-run

# 3. 手动跑一次
uv run research discover

# 4. 明确需要时安装每天 9:00 自动跑（macOS）
uv run research schedule launchd
#   ↳ 按提示 cp + launchctl load 即可
```

## CLI 子命令

### `uv run research discover [--dry-run] [--source X] [-c path]`

按 YAML 配置跑完整流水线：realtime signal → evidence → freshness/dedupe/ranking
→ coverage-aware briefing。

- `-c / --config <path>`：YAML 路径（默认 `config/discovery.yaml`）。
- `--dry-run`：列出每个 source 会跑什么，**不联网**。
- `--source <name>`：仅跑某个 source（`github|papers|wechat|hackernews|x`），可重复。
- `-o / --output-root <path>`：覆盖 YAML 里的 `output_root`（仅本次）。

退出码：`0` 全成功；`1` 有 source 部分失败；`2` 配置错误。

### `uv run research schedule <platform>`

打印安装步骤。

- `launchd`：渲染 macOS plist，附 `cp` + `launchctl load` 命令。
- `cron`：渲染 crontab 片段。

### `uv run research init-config [-o path] [--force]`

把 `config/discovery.yaml.example` 拷到目标位置。`config/discovery.yaml` 已经在 `.gitignore` 里，不会污染 git。

## 配置 schema

完整示例见 `config/discovery.yaml.example`，以下是字段速查：

```yaml
output_root: output                  # 相对 REPO_ROOT；默认 ./output
log_dir: .state/discovery            # 每次运行的 .log 文件

sources:
  github:
    enabled: true
    repos:                            # 直接指定 owner/repo 列表
      - anthropics/claude-code
    search:                          # 关键词搜索（gh search repos，按 updated）
      - query: "agent harness"
        limit: 10

  papers:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL] # 必须是 collect/papers.py:17-26 支持的分类
    max_per_category: 10

  wechat:
    enabled: true                    # optional News provider；public index 仍可能触发验证
    urls: []                         # optional 直接全文链接
    accounts:
      - {name: 架构师, wechat_id: JiaGouX}
    index_limit: 10

  hackernews:
    enabled: true
    feeds: [newstories, showstories]
    keywords: [agent, llm, claude, openai]
    limit: 20

  x:
    enabled: false                   # 不在 config 写 token value
    queries: ["(agent OR llm) lang:en -is:retweet"]
    token_env: X_BEARER_TOKEN
    limit: 10

briefing:
  enabled: true
  mode: signals                      # explicit digest / reading-list 保留为 legacy mode
  keyword: daily
  sources: [wechat, hackernews, x, github, papers]
  freshness_hours: 48                # inclusive lower boundary；上限 72
  hackernews_items: 3
  wechat_min_items: 0                # optional，不足不形成 required shortfall
  wechat_max_items: 2                # 独立 WeChat source 最多 2 条
  x_items: 0
  github_items: 1
  paper_items: 1
  since_days: 1                      # legacy mode only

limits:
  max_github_search_calls: 5         # 防爆 GitHub quota
  max_paper_categories: 5
  skip_if_already_collected_hours: 20   # 同一 owner/repo 距上次 < 20h 跳过
```

`.state/discovery/` 是未配置 `log_dir` 时的新 default。已有 `config/discovery.yaml`
如果仍显式写着 `.ai/L4-session/discovery`，会继续使用旧目录；需要切换时请手动改为
`.state/discovery`。migration 不会自动移动或删除旧 log，旧目录仍受原有
`limits.max_log_files` retention 约束。

## 去重 & 限流

- **GitHub repo**：`{owner}-{repo}` 目录在 `output/github/` 下存在，且 mtime < `skip_if_already_collected_hours`，跳过。
- **GitHub search**：始终跑，按 recent update 取 evidence，不直接当 social trend。
- **arXiv**：始终跑（按 `submittedDate desc` 拉新）。
- **WeChat**：直接 URL 可跳过近期已抓取项；account index CAPTCHA/空页/缺时间戳是 failure。
- **Hacker News / X**：按 current feed/recent-search 更新 archive，保留同一 item 首次 `discovered_at`。
- **Source mix**：按 Hacker News / WeChat / X / GitHub / arXiv 独立定额；HN 指向 github.com 仍归 Hacker News。HN attribution 仍链接讨论页，标题链接原文。
- **搜索 / 分类上限**：见 `limits.*`，超出部分标记 `skipped` 但不报错。

## 调度

### macOS launchd（推荐）

```bash
uv run research schedule launchd
```

输出会包含：

```text
# macOS launchd install (9:00 AM every day)
mkdir -p /Users/<you>/Library/LaunchAgents
cp /path/to/scripts/launchd/com.ai-intel-station.daily.plist /Users/<you>/Library/LaunchAgents/
launchctl load -w /Users/<you>/Library/LaunchAgents/com.ai-intel-station.daily.plist
```

验证：

```bash
launchctl list | grep com.ai-intel-station.daily
tail -f /tmp/ai-intel-station.daily.out
tail -f /path/to/repo/.state/discovery/*.log
```

停止 / 卸载：

```bash
launchctl unload ~/Library/LaunchAgents/com.ai-intel-station.daily.plist
rm ~/Library/LaunchAgents/com.ai-intel-station.daily.plist
```

### Linux / 任意 cron

```bash
uv run research schedule cron
# 把打印的 7 9 * * * 行贴到 crontab -e
```

## 常见问题

### `gh: command not found`

`collect/github.py` 依赖 `gh` CLI（`brew install gh && gh auth login`）。未安装时 GitHub source 会全部 fail；其它 source 不受影响。

### `Camoufox` / WeChat 抓取失败

先运行 `uv sync --extra wechat` 安装 optional browser stack。WeChat 有反爬，可能被风控；
default quota 仅将 WeChat 作为 optional News provider，最多 2 条；如果 HN/X 中至少一个
viable News source 完成，单独的 WeChat failure 会保留在报告中但不会降低 outcome。如果
WeChat 是唯一尝试的 News provider 且失败，仍会得到 `partial` 或 `coverage_incomplete`。
不需要 WeChat 时可将 `wechat_max_items` 调成 0 并关闭 source。直接全文抓取才需要
optional browser stack。

### `Failed to fetch arXiv: Tunnel connection failed`

沙箱 / 代理挡住了 arXiv。在公司网络或 VPN 内重试。

### 配置改了，runner 没生效

`research discover` 每次启动都重新加载 YAML；不需要重启服务。

### 想跑全量不跳过任何 repo？

临时把 `limits.skip_if_already_collected_hours: 0` 即可。`0` 表示"立刻重抓"。

## 运行日志

每次 `research discover` 会创建 `.state/discovery/<timestamp>.log`，包含：

- 每个 source 的 section 标题 + 成功 / 跳过 / 失败计数
- 最终 JSON 摘要（含 output_paths、briefing 路径与 status）

Signal status 是 `ready|partial|no_fresh_signals|coverage_incomplete`；生成崩溃是
`failed`，dry-run 是 `dry_run`，显式 digest/reading-list 是 `legacy`。
`coverage_incomplete` 不等于“今天没更新”。

CLI 最后会打印一行 `📓 Log: <path>`。

### 日志轮转

`limits.max_log_files` 控制 `.state/discovery/` 下保留的 log 文件数：

- **默认 30**：连续跑一个月也只保留最新 30 个；老的自动删。
- **0**：不轮转，想看多久看多久（注意磁盘）。
- 选 **>30** 也行，比如 `max_log_files: 365` 想存一整年。

轮转发生在**每次新 run 开始时**——不打扰正在写的 log，跑完才生效。

## 测试

```bash
# Core discovery tests
uv run --extra dev python -m pytest tests/test_agent_first_runtime.py tests/test_discovery_config.py

# Runner 的 free-function compatibility suite 使用 unittest
uv run python -m unittest tests.test_discovery_runner

# WeChat tests 按需加载 optional source dependency
uv run --extra wechat --extra dev python -m pytest -m wechat \
  tests/test_research_item.py tests/test_wechat_collect.py
```

覆盖 YAML 校验、fixture collector、credential boundary、freshness/timezone、去重/佐证/排名、
status/partial coverage、legacy compatibility 与 optional runtime boundary。
