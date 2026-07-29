# System 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/system.md`
> 验证日期: 2026-07-29

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Local-First Operation | Operator completes a research workflow | `research/cli.py`, `library/`, `briefing/` | `tests/test_restructure_research_architecture.py`, `tests/test_cli_e2e.py` | ✅ verified |
| Shared Local Archive Truth | Collected item becomes available to all surfaces | `library/items.py`, `library/storage.py`, `workspace_web/service.py` | `tests/test_e2e_archive.py`, `tests/test_service_e2e.py` | ✅ verified |
| Raw and Derived Output Separation | Save raw and derived artifacts | `collect/`, `publish/obsidian.py` | `tests/test_e2e_archive.py`, `tests/test_obsidian_publish.py` | ✅ verified |
| Unified Documented Entrypoint | Operator follows documented commands | `research/cli.py`, `pyproject.toml`, `.github/workflows/validate.yml` | `tests/test_l3_requirements.py`, `tests/test_cli_e2e.py`, `tests/test_release_artifact_checker.py`, CI installed-wheel CLI/Web smoke | ✅ verified |
| Explicit and Partial Failure Reporting | One part of a multi-source operation fails | `research/cli.py`, `briefing/reports.py`, `research/discovery/runner.py` | `tests/test_l3_subspec_e2e.py`, `tests/test_restructure_research_architecture.py`, `tests/test_discovery_runner.py` | ✅ verified |

## Reverse traceability

未发现需要新增 system-level Requirement 的 core public behavior；domain-specific behavior 进入对应 capability。
