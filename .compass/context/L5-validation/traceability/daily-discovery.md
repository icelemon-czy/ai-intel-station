# Daily Discovery 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/daily-discovery/spec.md`
> 验证日期: 2026-07-27

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Config Initialization and Validation | Initialize first-run config | `research/cli.py::run_init_config`, `research/discovery/config.py` | `tests/test_discovery_cli.py`, `tests/test_discovery_config.py` | ✅ verified |
| Network-Free Dry Run | Preview a configured sweep | `research/discovery/runner.py` | `tests/test_discovery_runner.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Selective and Fault-Isolated Sweep | Run selected sources | `research/discovery/runner.py` | `tests/test_discovery_runner.py` | ✅ verified |
| Optional Briefing Stage | Collect without briefing | `research/discovery/runner.py` | `tests/test_discovery_runner.py` | ✅ verified |
| Persistent Run Log and Read-Only Status | New default, status/list, explicit path and legacy sentinel Scenarios | `research/discovery/config.py`, `log.py`, `research/cli.py` | `tests/test_discovery_state_migration.py`, `tests/test_discovery_log.py` | ✅ verified |
| Explicit Schedule Installation | Inspect instructions and fresh cron bootstrap | `research/discovery/scripts.py` | `tests/test_schedule_install.py`, `tests/test_discovery_state_migration.py` | ✅ verified |
| Web-Triggered Discovery Run | Web starts discovery with configured log directory | `workspace_web/service.py` | `tests/test_discovery_web.py`, `tests/test_discovery_state_migration.py`, `web/test/discoveryCard.*.test.mjs` | ✅ verified |
| Agent-Operated Daily Intelligence | Ask what is worth reading today | `.agents/skills/daily-discovery/SKILL.md` | `tests/test_agent_first_runtime.py`; 第二次 fresh-context forward test（区分 dry-run/旧 briefing，在 network approval 不可用时明确返回 local fallback） | ✅ verified |
| Agent-Operated Daily Intelligence | Set up a first daily sweep | `.agents/skills/daily-discovery/SKILL.md` | `tests/test_agent_first_runtime.py`; 2026-07-27 isolated fresh-context forward test（真实修改 ignored config + dry-run + parsed YAML comparison） | ✅ verified |

## Reverse traceability

未发现 core Daily Discovery behavior 缺少主 Spec。Preference write 的 fresh-context test
只改变 GitHub search，未涉及的 source、repo、briefing、limits 与 private WeChat URL 均保持一致。
