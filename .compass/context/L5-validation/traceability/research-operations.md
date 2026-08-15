# Research Operations 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/research-operations/spec.md`
> 验证日期: 2026-08-13

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Unified Command Surface | List supported operations | `research/cli.py::build_parser` | `tests/test_cli_e2e.py`, `tests/test_l3_requirements.py` | ✅ verified |
| Unified Command Surface | Dispatch collection by source | `research/cli.py` | `tests/test_restructure_research_architecture.py` | ✅ verified |
| Local Read Actions Avoid Remote Fetch | Query local library | `research/cli.py`, `library/query.py` | `tests/test_l3_subspec_e2e.py` | ✅ verified |
| Local Web Workspace Entry | Start Web workspace from a nested working directory | `research/cli.py`, `workspace_web/server.py`, built Web package data | `tests/test_web_workspace.py`, `tests/test_release_artifact_checker.py`, `scripts/check_release_artifacts.py`, CI installed-wheel Web HTTP + referenced-asset smoke | ✅ verified |
| Read-Only Operational Inspection | Inspect the latest discovery run | `research/cli.py::run_discover_status` | `tests/test_discovery_state_migration.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Lightweight Core Runtime | Bootstrap the default operator environment | `pyproject.toml`, `uv.lock`, `collect/wechat.py`, split CI gates | `tests/test_agent_first_runtime.py`; core-only 422 passed + 3 subtests；runner 15 passed；CI installed-wheel `research --help` | ✅ verified |
| Lightweight Core Runtime | Install an optional source runtime | `pyproject.toml[project.optional-dependencies.wechat]`, `uv.lock`, `wechat` marker | isolated offline frozen sync-plan；真实安装 44 optional packages；16 marked tests passed；live e2e 由 operator URL gate 控制 | ✅ verified |
| Discovery-Only Social Source Selection | Select HN/X without expanding standalone collect | `research/cli.py`, `research/discovery/runner.py` | `tests/test_discovery_cli.py`, `tests/test_realtime_signals.py` | ✅ verified |

## Reverse traceability

`discover`、`schedule` 与 Agent Workflow detail 由 `daily-discovery` Spec 覆盖；source semantics
由 `signal-discovery` Spec 覆盖。
