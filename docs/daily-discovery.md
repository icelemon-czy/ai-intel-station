# Daily Discovery — 自动每日探索

一键把 AI Intel Station 从"手动敲命令"升级为"每天 9 点自动收集 + 出简报"。

## 60 秒上手

```bash
cd /path/to/ai-intel-station

# 1) 拷贝示例配置（首次）
uv run research init-config

# 2) 不联网试运行（确认 YAML 合法 + 看会跑什么）
uv run research discover --dry-run

# 3) 安装每日 9:00 自动跑（macOS 一键版）
uv run research schedule launchd --install

# 4) 任何时候查看上次跑了啥
uv run research discover --status
uv run research discover --log-list 7    # 最近 7 次 summary（一行一条）

# 5) 找生成的简报 markdown（如果忘了存在哪里）
uv run research briefing --list
```

到这里你已经"配好每日自动"。下面只在你需要时看。

## 完整上手

```bash
# 1. 拷贝示例配置（首次）
uv run research init-config
#   ↳ 在 config/discovery.yaml.example 的基础上写入 config/discovery.yaml

# 2. 按需编辑（GitHub repos / 搜索词 / arXiv 分类 / WeChat URLs）
$EDITOR config/discovery.yaml

# 3. 试运行（不联网，只看会跑什么）
uv run research discover --dry-run

# 4. 手动跑一次
uv run research discover

# 5. 安装每天 9:00 自动跑（macOS）
uv run research schedule launchd
#   ↳ 按提示 cp + launchctl load 即可
```

## CLI 子命令

### `uv run research discover [--dry-run] [--source X] [-c path]`

按 YAML 配置跑完整流水线：GitHub → arXiv → WeChat → briefing。

- `-c / --config <path>`：YAML 路径（默认 `config/discovery.yaml`）。
- `--dry-run`：列出每个 source 会跑什么，**不联网**。
- `--source <name>`：仅跑某个 source（`github` / `papers` / `wechat`），可重复。
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
log_dir: .ai/L4-session/discovery    # 每次运行的 .log 文件

sources:
  github:
    enabled: true
    repos:                            # 直接指定 owner/repo 列表
      - anthropics/claude-code
    search:                          # 关键词搜索（gh search repos，按 stars）
      - query: "agent harness"
        limit: 10

  papers:
    enabled: true
    categories: [cs.AI, cs.LG, cs.CL] # 必须是 collect/papers.py:17-26 支持的分类
    max_per_category: 10

  wechat:
    enabled: false                   # OFF by default
    urls: []                         # mp.weixin.qq.com 链接列表

briefing:
  enabled: true
  mode: reading-list                 # 或 digest
  keyword: daily                     # 输出路径 = briefing/<mode>s/<keyword>-<date>.md
  sources: [github, papers, wechat]
  since_days: 1                      # 仅过去 N 天

limits:
  max_github_search_calls: 5         # 防爆 GitHub quota
  max_paper_categories: 5
  skip_if_already_collected_hours: 20   # 同一 owner/repo 距上次 < 20h 跳过
```

## 去重 & 限流

- **GitHub repo**：`{owner}-{repo}` 目录在 `output/github/` 下存在，且 mtime < `skip_if_already_collected_hours`，跳过。
- **GitHub search**：始终跑（搜索结果是时间敏感的）。
- **arXiv**：始终跑（按 `submittedDate desc` 拉新）。
- **WeChat**：URL 已存在于 `output/wechat/*/research-item.json` 时跳过。
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
tail -f /path/to/repo/.ai/L4-session/discovery/*.log
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

`collect/wechat.py` 需要 Camoufox + 浏览器内核。WeChat 有反爬，可能被风控。建议默认 `enabled: false`，只在需要时打开。

### `Failed to fetch arXiv: Tunnel connection failed`

沙箱 / 代理挡住了 arXiv。在公司网络或 VPN 内重试。

### 配置改了，runner 没生效

`research discover` 每次启动都重新加载 YAML；不需要重启服务。

### 想跑全量不跳过任何 repo？

临时把 `limits.skip_if_already_collected_hours: 0` 即可。`0` 表示"立刻重抓"。

## 运行日志

每次 `research discover` 会创建 `.ai/L4-session/discovery/<timestamp>.log`，包含：

- 每个 source 的 section 标题 + 成功 / 跳过 / 失败计数
- 最终 JSON 摘要（含 output_paths、briefing 路径）

CLI 最后会打印一行 `📓 Log: <path>`。

### 日志轮转

`limits.max_log_files` 控制 `.ai/L4-session/discovery/` 下保留的 log 文件数：

- **默认 30**：连续跑一个月也只保留最新 30 个；老的自动删。
- **0**：不轮转，想看多久看多久（注意磁盘）。
- 选 **>30** 也行，比如 `max_log_files: 365` 想存一整年。

轮转发生在**每次新 run 开始时**——不打扰正在写的 log，跑完才生效。

## 测试

```bash
# 不依赖 pytest（venv 里没装），用 stdlib unittest：
.venv/bin/python -m unittest tests.test_discovery_config tests.test_discovery_runner
```

19 个测试覆盖：YAML 校验 / 错误信息 / dry-run / 去重 / 单 source 过滤 / briefing 写入。