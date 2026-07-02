---
name: daily-discovery
description: "Set up or operate the daily discovery sweep (GitHub + arXiv + WeChat + briefing) that AI Intel Station can run unattended via launchd / cron. Use when: 自动探索, 每日收集, daily discovery, schedule, launchd, cron, 定时, 自动跑, schedule daily, 每日简报."
argument-hint: "What the user wants (e.g., 'install the daily launchd schedule', 'run today's sweep now', 'show last run status')."
---

# Daily Discovery — 自动每日探索

AI Intel Station 的"自动收集 + 每日简报"工作流。
本 Skill 只做一件事：**让 discover / schedule / status 跑得对、用户看得懂**。

> 本 Skill 不写新代码；它通过 `uv run research discover|schedule|init-config|status` 这层 CLI 把"每日自动"装到用户机器上。

## 覆盖场景

| 触发关键词 | 走法 |
|:-----------|:-----|
| "自动探索 / 每日收集 / 每天 9 点 / schedule / 定时" | 走 §Setup（init-config → 编辑 → schedule） |
| "今天跑一下 / 立刻跑 / now run discover" | 走 §Run-now |
| "上次跑成啥样 / status / log" | 走 §Status |
| "我不想出简报 / 只收集 / no briefing" | 走 §Run-now 并提示 `--no-briefing` |

## Prerequisites

- 已经 `cd` 进 ai-intel-station 仓库
- Python 3.10+ + `uv`（已在系统 PATH）

## Procedure

### §Setup（用户第一次用）

1. 引导用户运行：
   ```bash
   uv run research init-config          # 写 config/discovery.yaml
   uv run research discover --dry-run   # 零联网试运行
   ```
2. **不要**替用户改 `config/discovery.yaml`——那是用户的偏好。让用户用 `$EDITOR` 改。
3. 询问平台：
   - **macOS**：`uv run research schedule launchd --install`（一键写入 `~/Library/LaunchAgents/` + `launchctl load`）
   - **Linux / 其他**：`uv run research schedule cron`（打印 crontab 片段）
4. 完成后给用户一行 `Verify` 命令：
   - macOS：`launchctl list | grep com.ai-intel-station.daily`
   - cron：`crontab -l | grep ai-intel-station`

### §Run-now（用户想立刻跑一次）

- 完整跑：`uv run research discover`
- 只跑一个 source：`uv run research discover --source github,papers`
- 不要简报：`uv run research discover --no-briefing`
- 仅预览：`uv run research discover --dry-run`

跑完告知用户：
- 摘要行（`📊 Summary: succeeded=X skipped=Y failed=Z`）
- 日志路径（`📓 Log: …`）
- 如果 failed>0，引导 `cat` 该 log

### §Status（用户问"上次咋样"）

- `uv run research discover --status`：只读最近一次 log 的 Summary + 时间戳，不重跑
- `uv run research discover --log-list N`：最近 N 次（每行一次），方便定位"哪几天失败了"
- `uv run research briefing --list`：列出已生成的 briefing markdown 文件，方便用户找到打开
- 若 log 不存在（从没跑过），提示 `uv run research discover --dry-run` 看看会跑什么

## Failure recovery

| 现象 | 修法 |
|:-----|:-----|
| `❌ invalid source 'foo'` | `--source` 只接受 `github|papers|wechat` |
| `gh: command not found` | `brew install gh && gh auth login`；其它 source 不受影响 |
| `Camoufox` 启动失败 | wechat 默认 off，先 `enabled: false` |
| `Tunnel connection failed` | 沙箱/公司网挡了 arXiv，换网再试 |
| YAML 解析报 `DiscoveryConfigError` | 直接念给用户：第几行哪个字段错了；不修配置，让用户改 |

## 退出码

| Code | 含义 |
|:-----|:-----|
| 0 | 全部成功 |
| 1 | 部分 source 失败（看 log） |
| 2 | 配置错误（YAML 不合法） |

## 不要做

- 不要直接编辑 `output/github/*/README.md` 或 `output/papers/*.md`——那是 collect 模块的产物
- 不要把 `config/discovery.yaml` commit 进去（已在 `.gitignore`）
- 不要替用户改 WeChat URL 列表——那是用户私域内容