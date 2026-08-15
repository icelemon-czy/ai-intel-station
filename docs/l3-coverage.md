# L3 Spec Coverage

当前 behavior source of truth 位于
[`.compass/context/L3-specs/specs/`](../.compass/context/L3-specs/specs/)。
详细 Requirement → implementation → test evidence 维护在
[`.compass/context/L5-validation/traceability/`](../.compass/context/L5-validation/traceability/)；
本页只保留 operator-facing overview，避免复制每条 Requirement。

| Capability | Main evidence surface | 2026-08-13 status |
|:-----------|:----------------------|:------------------|
| system | CLI、archive round-trip、partial failure tests | verified |
| collection | standalone + discovery-only source、archive/sidecar、credential/failure isolation tests | verified |
| signal-discovery | HN/X/WeChat fixtures、role/freshness、dedupe/corroboration、deterministic ranking tests | verified |
| github | repo/search/issues/sidecar/recency metadata/evidence role/CLI failure tests | verified |
| papers | category/list/fetch/persist/mixed-result/evidence role tests | verified |
| wechat | URL/content/image/sidecar + public-index attribution/coverage-failure tests | verified |
| library | ResearchItem/backfill/query/resilient loading + first-observation/role tests | verified |
| briefing | local modes + daily confidence/why-now/honest-empty/source-coverage tests | verified |
| research-operations | CLI help/dispatch/query/status + discovery-only HN/X + lightweight core tests | verified |
| web-workspace | service direct tests + Node render/controller tests | verified |
| daily-discovery | config/runner/log/schedule + Agent signal contract + backend/UI outcome tests | verified |

## Commands

```bash
# Lightweight core regression
uv sync --extra dev --frozen
uv run --frozen --extra dev python -m pytest -q tests \
  -m "not wechat" \
  --ignore=tests/test_discovery_runner.py \
  --ignore=tests/test_wechat_collect.py \
  --ignore=tests/test_wechat_e2e_live.py \
  --deselect=tests/test_web_workspace.py::test_npm_test_in_web_runs_node_test_suite
uv run --frozen --extra dev python -m unittest tests.test_discovery_runner

# Optional WeChat runtime
uv sync --extra dev --extra wechat --frozen
uv run --frozen --extra dev --extra wechat python -m pytest -q \
  -m wechat tests/test_research_item.py tests/test_wechat_collect.py

# Web + package
npm --prefix web ci
npm --prefix web run build
npm --prefix web test
uv build
uv run --frozen --extra dev python scripts/check_release_artifacts.py
uv venv --python 3.10 /tmp/ai-intel-wheel-smoke
uv pip install --python /tmp/ai-intel-wheel-smoke/bin/python dist/*.whl
/tmp/ai-intel-wheel-smoke/bin/research --help
/tmp/ai-intel-wheel-smoke/bin/python -I scripts/smoke_installed_wheel.py
```

local sandbox 可能禁止 `bind(2)` / `connect(2)`；此时 HTTP socket tests 必须明确记录为
skip 或 limitation，不能用静态检查冒充 full-stack verification。
