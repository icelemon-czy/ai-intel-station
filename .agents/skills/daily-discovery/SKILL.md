---
name: daily-discovery
description: "Operate AI Intel Station as an Agent-first daily intelligence loop: run or inspect discovery, read the resulting briefing, summarize today's useful items, update discovery preferences, or configure an explicitly requested schedule. Use for 今天有什么值得看、每日情报、自动探索、run/status/schedule；do not use for product code changes or an unrelated one-off source fetch."
---

# Daily Discovery — Agent-first 每日情报

把自然语言 intent 转成可验证的 discovery action，并直接把结果带回 conversation。
用户不需要学习 CLI、YAML、log directory 或 Web navigation。

```text
用户 intent
  → Agent 选择 setup / today / preferences / status / schedule
  → `uv run research ...` deterministic runtime
  → local signal archive + coverage-aware briefing + run log
  → Agent 读取 artifact status，返回结论与 Top items
```

## Boundary

- 复用 `research` CLI；不要在 Skill 中重新实现 collect、query、briefing 或 schedule。
- 允许正常 run 写入 `output/` 与 `.state/discovery/`。
- 用户要求首次使用、调整来源或跟踪主题时，允许创建或最小修改 ignored
  `config/discovery.yaml`，修改后必须 dry-run validation。
- 只有用户明确要求 install / 每天自动执行时，才修改 launchd 或其他本机 scheduler。
- Status、log inspection 和 briefing reading 必须只读且不得触发 network。
- 不启动 Web；Web 是 optional viewer，不是完成本 Workflow 的前置条件。
- 单独抓取一个 repo、paper category 或 WeChat URL 时，使用对应 source workflow，
  不把它扩张成 daily sweep。
- 用户说“我对 X 感兴趣，现在把相关内容拉下来”这类一次性 topic 拉取时，交给
  Interest Sweep Skill（`research seek`），不当成 Preferences；Preferences 只用于
  “以后每天跟踪”某来源或主题。
- 修改产品代码、测试或 Spec 时不触发本 Skill。

## Intent routing

| 用户 intent | Action |
|:------------|:-------|
| “今天有什么值得看 / 跑一下今日情报 / daily briefing” | Today |
| “以后每天都跟踪 agent memory / 只看 papers / 调整每日来源” | Preferences |
| “昨天跑得怎么样 / 为什么失败 / 最近几次状态” | Status |
| “每天 9 点自动跑 / 安装 schedule” | Schedule |
| “只收集，不生成 briefing” | Today + `--no-briefing` |
| “我对 X 感兴趣，现在把相关内容拉下来（一次性）” | 转 Interest Sweep Skill，不是 Preferences |

## Flow

### 1. Establish local state

1. 在 repository root 工作；先检查 `uv`、`config/discovery.yaml` 和最近 run state。
2. `uv` 不存在时，不要把安装命令甩给用户，也不要静默修改 global environment。
   请求一次 one-time install approval；获批后使用当前 platform 的可信 package manager
   或 official installer，验证 `uv --version` 后继续原始目标。
3. config 不存在且用户请求 run / setup 时，直接执行：

   ```bash
   uv run research init-config
   uv run research discover --dry-run
   ```

   bundled default 启用 WeChat public-index + Hacker News + GitHub + Papers；X 保持
   optional。默认 composition 是 3 条 Hacker News + optional、最多 2 条 WeChat +
   1 条 GitHub + 1 条 arXiv。不要让用户自己打开
   `$EDITOR` 才能继续。
4. config invalid 时读取完整 validation error。用户 intent 足够明确时直接最小修正；
   会改变来源、主题或 schedule 的歧义只问一个关键问题。

### 2. Today

1. 用户问“今天有什么”而未明确要求 rerun 时，先执行只读 status：

   ```bash
   uv run research discover --status
   uv run research briefing --list
   ```

2. 只有今日存在真实 `signals` briefing file，且对应 status 是
   `ready|partial|no_fresh_signals|coverage_incomplete`，才算可用 artifact。
   dry-run log 对应的 `dry_run`、`failed`、`legacy`、`briefing.path=(dry-run)`、
   stale artifact 或旧式空
   briefing 都不能当作今日结果，也不能成为跳过 real run 的理由。
3. 今日已有上述真实 artifact 时直接读取，不重复 network run。
   `no_fresh_signals` 只能解释为“完整覆盖下没有验证到新 signal”；
   `coverage_incomplete` 必须说“覆盖不完整，无法得出今日无新内容的结论”。
4. 没有今日真实结果、结果 stale，或用户明确要求 rerun 时执行：

   ```bash
   uv run research discover
   ```

   显式来源使用 `--source github,papers`；只收集使用 `--no-briefing`。
   如果当前 environment 的 network action 需要 approval，按 permission flow 请求；
   approval 不可用时明确说明“今天没有可验证的新结果”，再将旧库存标为 fallback，
   不能把旧内容包装成今天的 briefing。
5. 从 command output 定位 Summary、briefing status、log 和 briefing path。读取 signal
   artifact，按 arXiv / GitHub / Hacker News / WeChat 分组返回最多 7 条 item；每条说明“是什么”、
   “为什么现在值得看”、confidence 和 signal/evidence 来源。
   同时报告各 required source expected / actual / missing；WeChat 按独立 source
   报告 actual / optional maximum，缺少时不形成 required shortfall。Hacker News 指向
   github.com 的 story 仍归 Hacker News，不得改报成 GitHub news。
6. partial failure 或 quota shortfall 不丢弃成功结果。先返回可用 briefing，再单独说明
   failed source 与缺少的 lane/WeChat 数量。

### 3. Preferences

1. 读取现有 `config/discovery.yaml`，保留未涉及的 field 和 private URL。
2. 把用户明确表达的 source、repo、search topic、paper category、briefing mode
   最小写入 config；不要替用户扩大关注范围。
3. 写入后执行：

   ```bash
   uv run research discover --dry-run
   ```

4. 只报告实际改变的 preference 和 validation 结果，不倾倒完整 YAML。

### 4. Status

- 最近一次：`uv run research discover --status`
- 最近 N 次：`uv run research discover --log-list N`
- Briefing artifacts：`uv run research briefing --list`

直接读取相关 log 并解释根因。不要让用户自己 `cat` log 才能获得答案。
若从未运行，说明尚无 evidence，并执行 network-free dry-run preview；除非用户同时要求
正式收集，否则不自动联网。

### 5. Schedule

1. 只有用户明确要求自动执行时才进入本阶段。
2. macOS 使用：

   ```bash
   uv run research schedule launchd --install
   ```

3. Linux / cron 先生成 proposal：

   ```bash
   uv run research schedule cron
   ```

   用户已明确要求安装时执行 `uv run research schedule cron --install`。
4. 安装后由 Agent 运行 platform verification 并报告结果；不要把 verification command
   作为待办交还用户。

## Failure recovery

- `invalid source`：只接受 `github|papers|wechat|hackernews|x`，根据用户原始 intent 修正。
- `gh` 缺失或未登录：解释 GitHub source 不可用；Papers 等独立来源继续返回。
- WeChat public-index 验证码或 access block：保留 failure detail；另一个 viable realtime source
  已完成时按 optional failure 处理，否则标记 coverage incomplete。不要把它说成“公众号今天没更新”。
- X token 缺失：报告配置的 env name，不发 request，不阻断 Hacker News / WeChat。
- network 或 sandbox 阻断：如执行目标必须联网，按当前环境 permission flow 请求一次授权；
  不能授权时返回已存在的 local briefing。
- `DiscoveryConfigError`：报告具体 field；能从明确 intent 恢复时由 Agent 修复并重新 dry-run。
- command exit 1 表示 partial source failure；exit 2 表示 config error，不得混为全量失败。

## Output

优先返回用户价值，不返回 command transcript：

- 今日结论或 run/status 结论
- 按 arXiv / GitHub / Hacker News / WeChat 分组的最多 7 条重点内容
- required source 的 expected / actual / missing，以及 WeChat actual / optional maximum
- succeeded / skipped / failed source
- briefing 与 log 的 clickable local path
- 需要用户决策的唯一 blocker（如果存在）

## Trigger checks

Positive:

- “今天 AI 圈有什么值得看？”
- “现在跑一遍每日情报，按 arXiv、GitHub 和 Hacker News 分组给我重点。”
- “每天早上九点自动收集，昨天失败的话告诉我原因。”
- “把每日搜索主题改成 agent memory。”

Negative:

- “实现一个新的 Twitter collector。” → product development
- “review discovery 的 test coverage。” → test audit
- “只抓取这个微信公众号 URL。” → one-off WeChat collection

## Anti-patterns

- 只把 CLI command 复制给用户，没有实际执行。
- 要求用户手改 YAML 或读 log 才能继续。
- 在 Skill 中解析远端 API、生成 sidecar 或复制 Python business logic。
- 为展示结果启动 Web server。
- 未经明确请求安装 schedule、改 crontab 或扩大 source scope。
- 直接修改 `output/` generated artifact，或 commit ignored personal config。
