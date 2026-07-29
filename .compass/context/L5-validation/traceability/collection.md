# Collection 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/collection/spec.md`
> 验证日期: 2026-07-29

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Supported Sources | Choose a collection source | `research/cli.py`, `workspace_web/service.py` | `tests/test_web_workspace.py`, `tests/test_l3_requirements.py` | ✅ verified |
| Archive and Sidecar Persistence | Persist a collected item | `collect/`, `library/items.py` | `tests/test_research_item.py`, `tests/test_e2e_archive.py` | ✅ verified |
| Source-Specific Validation and Errors | Required dependency is unavailable | `collect/github.py`, `collect/papers.py`, `collect/wechat.py`, `workspace_web/service.py` | `tests/test_service_e2e.py`, `tests/test_l3_http_e2e.py`, `tests/test_papers_atom_parse.py` | ✅ verified |
| Independent Progress | One paper category fails | `collect/papers.py`, `research/cli.py`, `research/discovery/runner.py` | `tests/test_l3_subspec_e2e.py`, `tests/test_discovery_runner.py` | ✅ verified |

## Reverse traceability

per-source details 已分别覆盖于 `github`、`papers` 与 `wechat` Spec。
