# WeChat 追溯矩阵

> 对应 Spec: `.compass/context/L3-specs/specs/wechat/spec.md`
> 验证日期: 2026-08-13

| Requirement | Scenario | Implementation | Test evidence | Status |
|:------------|:---------|:---------------|:--------------|:-------|
| Normalize Article URL | Pasted URL contains escaped or HTML separators | `collect/wechat.py::normalize_wechat_url` | `tests/test_wechat_collect.py` | ✅ verified |
| Preserve Article Content and Metadata | Collect an article | `collect/wechat.py::fetch_article` | `tests/test_research_item.py`, `tests/test_wechat_collect.py` | ✅ verified |
| Localize Article Images | Article contains supported image URLs | `collect/wechat.py` image pipeline | `tests/test_research_item.py`, `tests/test_wechat_collect.py` | ✅ verified |
| WeChat Sidecar | Load collected article | `library/items.py` | `tests/test_research_item.py` | ✅ verified |
| Explicit Runtime Failure | Article cannot be fetched | `collect/wechat.py`, `workspace_web/service.py` | `tests/test_service_e2e.py` | ✅ verified |
| Explicit Runtime Failure | WeChat extra is not installed | `collect/wechat.py::_load_wechat_runtime`, `research/cli.py::main` | `tests/test_agent_first_runtime.py`; core-only `research collect wechat …` returned exit 2 + install guidance，无 traceback | ✅ verified |
| Account Watchlist Discovery | Discover attributable watchlist article | `collect/wechat_index.py`, `library/items.py` | `tests/test_realtime_signals.py` public-index fixtures | ✅ verified |
| Honest WeChat Discovery Coverage | CAPTCHA / empty / malformed / missing time | `collect/wechat_index.py`, `research/discovery/runner.py` | `tests/test_realtime_signals.py` coverage-failure fixtures | ✅ verified |

## Reverse traceability

live e2e 是 optional verification，不改变 product behavior；无 URL 时 skip 由
`tests/test_l3_requirements.py` 验证。optional dependency preflight 在 browser launch 前执行。
