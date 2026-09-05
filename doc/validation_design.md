# Validation

Validation 证明 current implementation 是否满足已记录的 observable behavior。测试优先跨真实 public boundary，避免只验证 helper、mock call 顺序或当前实现细节。

## 分层

| Layer | 主要 evidence | 目的 |
|:------|:--------------|:-----|
| Core | Python unit / integration tests | schema、parser、query、render、config 和 failure behavior |
| Boundary | subprocess、filesystem、local HTTP tests | 验证真实 CLI、archive round-trip 和 service contract |
| Discovery | fixture source + production selection path | 验证 freshness、role、dedupe、quota、coverage 与 partial failure |
| Optional WeChat | `wechat` marker 与 live opt-in | 隔离 heavy runtime 和外部反爬条件 |
| Web | Node tests + Python service/HTTP tests | 验证 UI state、API contract 和 bundled frontend |
| Release | build、artifact checker、installed-wheel smoke | 验证 package 包含可运行 CLI 与 static assets |

## Test design rule

- 测试 user-visible behavior 和 public boundary，不把 business function 替换成 fake 后声称完成 end-to-end 验证。
- 允许替换真正的 external boundary，例如 fake `gh` executable、local HTTP server 或 fixture response；production parser、orchestration 和 persistence 仍应实际执行。
- filesystem test 使用 temporary output root，不依赖 repository 内已有 archive。
- optional credential、browser 或 network prerequisite 缺失时显式 skip 或返回 limitation，不把静态检查冒充 live verification。
- 每个 assertion 对应真实 contract、risk 或 regression；green summary 本身不是 coverage 证明。

## Canonical commands

Core regression：

```bash
uv sync --extra dev --frozen
uv run --frozen --extra dev python -m pytest -q tests \
  -m "not wechat" \
  --ignore=tests/test_discovery_runner.py \
  --ignore=tests/test_wechat_collect.py \
  --ignore=tests/test_wechat_e2e_live.py
uv run --frozen --extra dev python -m unittest tests.test_discovery_runner
```

Optional WeChat：

```bash
uv sync --extra dev --extra wechat --frozen
uv run --frozen --extra dev --extra wechat python -m pytest -q \
  -m wechat tests/test_research_item.py tests/test_wechat_collect.py
```

Web 与 release：

```bash
npm --prefix web ci
npm --prefix web run build
npm --prefix web test
uv build
uv run --frozen --extra dev python scripts/check_release_artifacts.py
```

Installed-wheel smoke 使用 `scripts/smoke_installed_wheel.py`。HTTP socket tests 在 restricted sandbox 可能无法执行 `bind(2)` 或 `connect(2)`；此时必须记录 limitation，并在允许 local socket 的环境补验证。

## Evidence map

- Library / collect：`tests/test_research_item.py`、`tests/test_e2e_archive.py`、`tests/test_cli_e2e.py`、`tests/test_library_catalog.py`
- System / HTTP boundary：`tests/test_system_contracts.py`、`tests/test_http_*_e2e.py`、`tests/test_source_contract_e2e.py`
- Daily Discovery：`tests/test_signal_config.py`、`tests/test_signal_collection.py`、`tests/test_signal_selection.py`、`tests/test_signal_rendering.py`、`tests/test_discovery_runner.py`
- Briefing / publish：`tests/test_briefing_reports.py`、`tests/test_obsidian_publish.py`
- Web：`tests/test_web_backend.py`、`tests/test_web_http_preview.py`、`tests/test_service_e2e.py` 与 `web/test/`；frontend behavior 只在 Node suite 验证
- Release：`tests/test_release_artifact_checker.py`、`scripts/check_release_artifacts.py`
