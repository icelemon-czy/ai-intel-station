# Daily Discovery 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/daily-discovery/spec.md`
> 验证日期: 2026-08-14

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Config Initialization and Validation | Initialize viable 5/2/1/1 config | `research/cli.py::run_init_config`, `research/discovery/config.py` | `tests/test_discovery_cli.py`, `tests/test_discovery_config.py`, `tests/test_realtime_signals.py`; personal network-free dry-run | ✅ verified |
| Config Initialization and Validation | Reject positive quota without viable source | `research/discovery/config.py::_validate_signal_quota_sources` | `tests/test_realtime_signals.py` absent/disabled/no-target/explicit-empty aggregate assertions | ✅ verified |
| Network-Free Dry Run | Preview a configured sweep | `research/discovery/runner.py` | `tests/test_discovery_runner.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Selective and Fault-Isolated Sweep | Run selected realtime sources | `research/discovery/runner.py` | `tests/test_realtime_signals.py`, `tests/test_discovery_runner.py` | ✅ verified |
| Optional Briefing Stage | Collect without briefing | `research/discovery/runner.py` | `tests/test_discovery_runner.py` | ✅ verified |
| Persistent Run Log and Read-Only Status | New default, status/list, explicit path and legacy sentinel Scenarios | `research/discovery/config.py`, `log.py`, `research/cli.py` | `tests/test_discovery_state_migration.py`, `tests/test_discovery_log.py` | ✅ verified |
| Explicit Schedule Installation | Inspect instructions and fresh cron bootstrap | `research/discovery/scripts.py` | `tests/test_schedule_install.py`, `tests/test_discovery_state_migration.py` | ✅ verified |
| Web-Triggered Discovery Run | Web starts discovery with configured log directory | `workspace_web/service.py` | `tests/test_discovery_web.py`, `tests/test_discovery_state_migration.py`, `web/test/discoveryCard.*.test.mjs` | ✅ verified |
| Agent-Operated Daily Intelligence | Return grouped default composition and partial quota | `.agents/skills/daily-discovery/SKILL.md` | `tests/test_agent_first_runtime.py`, `tests/test_realtime_signals.py` grouped artifact/shortfall assertions | ✅ verified |
| Agent-Operated Daily Intelligence | Set up a first daily sweep | `.agents/skills/daily-discovery/SKILL.md` | `tests/test_agent_first_runtime.py`; 2026-07-27 isolated fresh-context forward test（真实修改 ignored config + dry-run + parsed YAML comparison） | ✅ verified |
| Agent-Operated Daily Intelligence | Accept honest empty / preserve partial / reject dry-run-stale-legacy | `.agents/skills/daily-discovery/SKILL.md`, `research/discovery/log.py` | `tests/test_agent_first_runtime.py`, `tests/test_realtime_signals.py`, `tests/test_briefing_marker.py` | ✅ verified |
| Web-Triggered Discovery Run | Display structured daily outcome | `workspace_web/service.py`, `web/src/DailyDiscoveryCard.jsx` | `tests/test_briefing_marker.py`, `web/test/discoveryCard.ssr.test.mjs` | ✅ verified |

## Reverse traceability

未发现 core Daily Discovery behavior 缺少主 Spec。Preference write 的 fresh-context test
只改变 GitHub search，未涉及的 source、repo、briefing、limits 与 private WeChat URL 均保持一致。
