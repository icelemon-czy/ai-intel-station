# 验证报告 — Agent-first Gap Closure

> 日期: 2026-07-27
> Parent change: `add-agent-first-daily-intelligence`
> Result: PASS

## Scope

闭合 2026-07-25 validation report 中两个明确的 `partial`：

1. full WeChat optional runtime install
2. first-run / preference config write 的 isolated Agent forward test

本 follow-up 不改变 main Spec behavior，也不扩展 Web scope。

## Automated Tests Added

`tests/test_agent_first_runtime.py` 从 4 个扩展到 5 个 tests：

- 新增 isolated empty-cache、offline、frozen WeChat extra sync-plan test，断言
  BeautifulSoup、Camoufox、httpx、markdownify 与 Playwright 均进入 transitive plan。
- missing-extra test 从 mocked `fetch_article` 改为真实 subprocess + import guard；
  即使 dev machine 已安装 optional packages，也能验证 exit 2、install guidance 与无 traceback。
- WeChat suite 新增 `_load_wechat_runtime()` test，full extra 安装后自动断言
  `BeautifulSoup` 与 `AsyncCamoufox` runtime boundary 可 import。
- core dry-run 使用 temp config / temp log directory，不再污染 repository `.state/`。
- Skill contract 同时断言 preference write 必须保留未涉及 field、限制 scope 并 dry-run。

Command:

```text
UV_CACHE_DIR=/tmp/ai-intel-uv-cache \
  uv run --frozen python -m unittest tests.test_agent_first_runtime
```

Result: `5 passed`。

## Full WeChat Optional Install

实际执行：

```text
UV_CACHE_DIR=/tmp/ai-intel-uv-cache uv sync --extra wechat --frozen
```

Result:

- Playwright、LXML、Cython 与 NumPy 下载完成
- 44 optional packages 安装成功
- `_load_wechat_runtime()` 返回 `BeautifulSoup` 与 `AsyncCamoufox`
- WeChat/ResearchItem/Agent runtime suite: `42 passed, 1 skipped`
- skipped case 是未提供 `WECHAT_E2E_URLS` 的 live network e2e，未记作 live fetch success

验证后执行 default sync，卸载 49 个 optional/dev packages。final dry-run：

```text
Checked 2 packages
Would make no changes
```

因此 optional install Scenario 已验证，同时 default environment 仍保持 lightweight。

## Preference Fresh-context Forward Test

在 `/tmp` 创建独立 project copy 和 pre-existing ignored config。fixture 包含：

- 两条现有 GitHub search
- `anthropics/claude-code` repo
- Papers / WeChat / briefing / limits 配置
- private sentinel WeChat URL

fresh-context Agent 收到：

```text
把每日 GitHub 搜索主题改成 agent memory。保留其他 sources、repo、limits 和现有
private WeChat URL；不要安装 schedule。完成后直接告诉我改了什么和 dry-run 是否通过。
```

Agent 实际修改 isolated `config/discovery.yaml` 并运行 offline discovery dry-run。
Main Agent 随后独立解析 before/after YAML：

- GitHub search: 两条旧 query → `agent memory`，保留 `limit: 10`
- 所有未涉及 field 完全相等
- private WeChat URL 保留
- dry-run: `succeeded=5, skipped=0, failed=0`
- log 明确包含 `would search 'agent memory'`
- 未运行 scheduler、未启动 Web、未修改 product source/test/Spec

这条 evidence 验证了真实 Agent write behavior，不以 Skill 文案或 Agent 自报代替。

## Conclusion

两个旧 `partial` 均升级为 `verified`。仍未运行真实 WeChat article live fetch；
该 e2e 需要 user-provided URL，属于既有 optional live verification，不影响本次两个
Scenario 的闭合。

Final regression:

- Agent / CLI / discovery / schedule / Spec-context targeted surface: `63 passed`
- discovery runner unittest surface: `14 passed`
- core-only Agent runtime tests: `5 passed`
- `uv lock --check`: PASS
- `git diff --check`: PASS
- final default environment: `Checked 2 packages; Would make no changes`
- test-created config、repository `.state` log 与 isolated `/tmp` workspace 已清理
