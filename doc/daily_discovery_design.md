# Daily Discovery

Daily Discovery 是 Agent-first 的每日 AI 情报 loop。project Agent 解释自然语言 intent，`daily-discovery` Skill 调用 deterministic `research` CLI；runtime 收集 realtime signal 和 supporting evidence，生成带 coverage 状态的 briefing，Agent 再把重点返回 conversation。临时按某个主题一次性拉取相关内容不属于本 design：那是 `research seek` 的 Interest Sweep，见 [`interest_sweep_design.md`](interest_sweep_design.md)。

```text
Agent intent
    ↓
config validation → source sweep → archive + sidecar
                                  ↓
                    freshness / dedupe / quota
                                  ↓
                    signal briefing + run log
```

## Source role

| Source | 默认 role | 说明 |
|:-------|:----------|:-----|
| Hacker News | `signal` | realtime News；标题链接原文，attribution 保留 discussion link |
| WeChat public index / direct article | `signal` | optional News provider；index 必须提供可信 publication time |
| X recent search | `signal` | optional，依赖 bearer token，默认关闭 |
| GitHub repository/search | `evidence` | supporting evidence，不填补缺失的 News quota |
| arXiv paper | `evidence` | supporting evidence，按 publication time 排序 |

Daily Top item 必须由带可信 publication time 的 realtime `signal` 发起。Evidence 可以增强 corroboration，但不能单独发起 News item。HN 原文即使指向 GitHub，仍归 Hacker News lane，不重复计入 GitHub quota。

## 默认 composition 与 selection

默认配置尝试选择 3 条 Hacker News、最多 2 条 optional WeChat、1 条 GitHub 和 1 篇 arXiv；X quota 默认为 0。实际值由 `config/discovery.yaml` 控制，canonical schema 与 packaged example 位于 `src/ai_intel_station/discovery/`。

Selection 依次执行：

1. 只接受 freshness window 内且不过度 future-skew 的 source time。
2. 按 normalized URL、title 和 source identity 去重，同时保留跨 source corroboration。
3. 在各 source lane 内按 freshness、engagement 和确定性 tie-break 排序。
4. 应用独立 quota；某个 lane 不足不会由不相干 source 静默补位。
5. 输出 selected item、source coverage、quota shortfall 与 failure detail。

## Coverage status

| Status | 含义 |
|:-------|:-----|
| `ready` | required coverage 完整且有可用 item |
| `partial` | 有结果，但 required source、quota 或 attempted source 存在缺口 |
| `no_fresh_signals` | required coverage 完整，但 freshness window 内没有 item |
| `coverage_incomplete` | source failure 或未尝试的 required lane 使“没有更新”无法成立 |
| `failed` | briefing generation 自身失败 |
| `dry_run` | 只验证计划，不联网、不收集 |
| `legacy` | 显式运行 digest / reading-list mode |

WeChat 默认 optional：只要其他 viable News source 完成，单独的 WeChat failure 会被报告，但不自动把 outcome 降级；如果 WeChat 是唯一尝试的 News provider，失败仍会形成 incomplete coverage。

## 配置、日志与调度

- `research init-config` 从 packaged `src/ai_intel_station/discovery/discovery.yaml.example` 写出 ignored `config/discovery.yaml`。
- `research discover --dry-run` 验证 config 并列出计划，保证不触网。
- 每次 run 写入 `log_dir`；默认是 `.state/discovery/`，并由 `limits.max_log_files` 控制 retention。
- `research discover --status` 和 `--log-list N` 只读现有 run log，不重新执行。
- `research schedule launchd|cron` 默认打印安装步骤；只有显式 `--install` 才修改 scheduler。
- Direct WeChat article collection 才依赖 `wechat` extra；public-index watchlist 走 core runtime。

## Failure boundary

各 source 独立报告 success、skip 和 failure。一个 source 失败不会抹掉其他 source 已保存的 artifact；最终 status 必须区分 partial progress、完整空结果和 coverage 不完整。Credential、network、CAPTCHA、无 publication time 和 malformed response 都作为 source evidence 显式呈现。

## 入口与 evidence

- Agent surface：`.agents/skills/daily-discovery/SKILL.md`
- Runtime：`src/ai_intel_station/discovery/sources.py`、`src/ai_intel_station/discovery/runner.py`、`src/ai_intel_station/briefing/signals.py`、`src/ai_intel_station/briefing/signal_rendering.py`
- Config：`src/ai_intel_station/discovery/config.py` 负责 YAML/resource plumbing，`config_schema.py` 与 `config_validation.py` 负责 schema 和 line-aware validation
- Example：`src/ai_intel_station/discovery/discovery.yaml.example`
- Tests：`tests/test_signal_config.py`、`tests/test_signal_collection.py`、`tests/test_signal_selection.py`、`tests/test_signal_rendering.py`、`tests/test_discovery_runner.py`、`tests/test_discovery_cli.py`、`tests/test_discovery_config.py`、`tests/test_schedule_install.py`、`tests/test_discovery_web.py`
