# 测试规范

> 当前测试面已经收敛到根级 `tests/`，并围绕统一 operator surface 组织。WeChat 仍然拥有最完整的纯函数测试；GitHub / papers 仍以 smoke run 为主，但后续优先补到根级测试而不是继续分散在来源目录。

## 测试框架

| 类型 | 框架 / 方式 | 主线 |
|------|-------------|------|
| Core regression | `pytest` + `dev` extra | broad-discover non-WeChat tests；排除 runner compatibility module 与 npm wiring |
| Discovery runner | `unittest` | 单独加载 free-function compatibility adapter，避免 pytest 重复收集 `self` |
| WeChat optional | `pytest` + `wechat` marker | 安装 `dev,wechat` extra 后运行 optional runtime / collection tests |
| Web | Node test + Vite | clean install、build、全部 Node tests；CI 必须允许 loopback |
| Release artifact | `uv build` + checker + installed-wheel smoke | wheel/sdist 必须包含 Web static 引用，且不得包含 private runtime data；安装后验证 CLI 与 real HTTP assets |
| WeChat live e2e | `pytest` + `e2e` marker | 仅在 operator 提供 `WECHAT_E2E_URLS` 时运行 |

## 测试文件约定

- **命名**: `test_*.py`
- **位置**: 根级 `tests/`
- **测试命名模式**: `test_xxx`，必要时配合 `pytest.mark.parametrize`

## 测试结构规范

### 单元测试

- 优先覆盖纯转换函数，例如 URL 归一化、Markdown 组装、sidecar 解析与子命令 dispatch
- 只 mock 外部依赖，不 mock 同文件的纯函数拼装逻辑
- 使用 `tmp_path` 做文件落盘断言，避免污染仓库目录
- 对文本转换优先断言关键字段和链接，而不是整篇长文本逐字匹配

### Live E2E

- 只有在明确需要验证真实抓取链路时才跑
- 通过 `WECHAT_E2E_URLS` 提供 URL；未设置时应 `skip`
- live e2e 重点断言“生成了 Markdown 且包含源 URL / 图片落盘”，不要写脆弱的全文匹配

### CLI smoke

- GitHub / papers 修改后至少跑一次最小 happy path
- smoke 验证必须检查生成文件是否实际写入 `output/`，不只看终端输出
- 如果外部依赖不可用，在变更说明里明确写明阻塞点，而不是假装已验证

## 覆盖要求

- 不设全仓统一覆盖率阈值
- WeChat 的新增纯逻辑优先补 `tests/test_wechat_collect.py`
- operator surface 的参数和 dispatch 变化优先补 `tests/test_restructure_research_architecture.py`
- dependency boundary 变化必须验证 default sync 不包含 optional/test stack，并用 import guard
  防止 dev environment 中已安装的 package 掩盖 core startup coupling
- 需要 optional runtime 的 test MUST 使用对应 marker；core gate 不得靠本机已安装 package
  偶然变绿
- optional extra packaging test 使用 isolated `UV_PROJECT_ENVIRONMENT`、empty cache、
  `UV_OFFLINE=1` 与 frozen dry-run，断言 transitive runtime 出现在 install plan；release
  verification 再真实安装 extra、import public runtime boundary，并恢复 default environment
- missing optional dependency 必须通过真实 subprocess + import guard 验证，不只 mock
  已知 exception；同时断言 non-success、install guidance 与无 traceback
- Agent Skill 的 config write behavior 使用 isolated workspace forward test，并对 parsed
  config 做 before/after comparison；Agent 自报成功不能替代 artifact 与 dry-run evidence
- HTTP test 使用 kernel-assigned loopback port 并等待真实 readiness；禁止固定共享 port 或
  只看到 pre-bind banner 就当 server 已启动
- remote source test 必须把 network boundary 指向 local fixture，并把 output_root 指向
  temporary directory；不得把 live response 写进 repository `output/`
- test assertion 绑定 main Spec 与 frontend consumer 使用的 response contract，不绑定
  capitalization、旧 response key 或无 Requirement 支撑的 status code
- GitHub / papers 一旦开始有复杂分支、重试或格式转换，优先补 `tests/` 而不是长期依赖 smoke run

## 反模式

- ❌ 用真实网络请求代替本可写成纯函数测试的场景
- ❌ 不设置 `WECHAT_E2E_URLS` 却把 live e2e 失败当代码缺陷
- ❌ smoke run 只看 `print("Saved")`，不检查落盘内容
- ❌ 为了通过测试而改 `output/` 样例，而不改生成器逻辑
- ❌ remote failure 被转换成 empty list 后继续报告 `success`

## Release Commands

```bash
# Lightweight core
uv sync --extra dev --frozen
uv run --frozen --extra dev python -m pytest -q tests \
  -m "not wechat" \
  --ignore=tests/test_discovery_runner.py \
  --ignore=tests/test_wechat_collect.py \
  --ignore=tests/test_wechat_e2e_live.py \
  --deselect=tests/test_web_workspace.py::test_npm_test_in_web_runs_node_test_suite
uv run --frozen --extra dev python -m unittest tests.test_discovery_runner

# Optional WeChat
uv sync --extra dev --extra wechat --frozen
uv run --frozen --extra dev --extra wechat python -m pytest -q \
  -m wechat tests/test_research_item.py tests/test_wechat_collect.py

# Web and release artifacts
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
