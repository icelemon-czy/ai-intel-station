# 验证报告 — Agent-first Daily Intelligence

> 日期: 2026-07-25
> Change: `add-agent-first-daily-intelligence`
> Review: PASS（Main Agent fallback verify）
> Follow-up: 2026-07-27 两个 non-blocking partial 均已闭合；详见
> `2026-07-27-agent-first-gap-closure.md`

## Scope

- 将 `daily-discovery` 从 CLI tutorial 改为 Agent-operated Workflow
- 保留 `research` CLI 作为 deterministic runtime，Web 降为 optional viewer
- 将 default environment 收敛为 project + PyYAML
- 将 WeChat browser stack 与 pytest 拆为 `wechat` / `dev` optional extras
- 为缺失 WeChat extra 提供 non-success、可执行 guidance 且不泄漏 traceback

## Commands and Results

| Command / surface | Result |
|:------------------|:-------|
| `uv lock --check` | PASS，56 packages 可解析 |
| `uv sync --frozen` + `uv sync --dry-run --frozen` | PASS，default environment 检查 2 packages 且无需变更 |
| `uv run --frozen research --help` | PASS |
| `uv run --frozen research discover --dry-run --config config/discovery.yaml.example` | PASS，GitHub/Papers plan 可运行，WeChat default disabled |
| core-only `uv run --frozen research collect wechat …` | PASS，exit 2，输出 `uv sync --extra wechat` guidance，无 traceback |
| Agent/discovery targeted pytest surface | 62 passed |
| `python -m unittest tests.test_discovery_runner` | 14 passed |
| WeChat normalization/timestamp/title + ResearchItem tests | 36 passed |
| post-merge Spec/context tests | 19 passed |
| business Spec structure | PASS，10 Spec domains、55 Requirements、64 Scenarios；无 incomplete / duplicate Requirement |
| project-local Skill inventory/frontmatter/wrapper validation | PASS，10 个 canonical Skills，无 duplicate name |
| fresh-context Today intent forward test（第一次） | BLOCKED，Agent 自行读取 status/list 且未启动 Web，但把 dry-run 当作停止依据；触发 review-repair loop |
| fresh-context Today intent forward test（第二次） | PASS，明确拒绝把 dry-run/旧 briefing 当作 today artifact；无 network approval 时返回清晰 local fallback |
| `git diff --check` | PASS |

## Scenario Evidence

### Today intelligence

第一次 fresh-context Agent 收到“今天 AI 圈有什么值得看？”后：

1. 先运行 read-only status/list。
2. 识别今日只有 dry-run、没有 real new intelligence。
3. 读取 local inventory，返回 3 条具体内容和 artifact path。
4. 没有把 CLI、YAML、log 或 Web 操作转交给 user。

它没有把旧内容冒充成“今天”，但也没有进入 Skill 规定的 real run / network permission
分支，因此不能算 PASS。Main Agent 将 change 回流到 `review-failed → implementing`，
收紧 dry-run decision rule 后重新执行 fresh-context test。

第二次 fresh-context test 在相同 prompt 下读取了 status、briefing、log 与 local inventory：

1. 将今日 `dry_run` 明确判定为非真实 collection。
2. 因评测环境没有 external network approval，明确返回“今天没有可验证的新情报结果”。
3. 将旧 inventory 标为“非今日参考”，没有包装成 today briefing。
4. 没有启动 Web，也没有要求 user 自行运行 CLI、编辑 YAML 或读取 log。

因此 Today Scenario 在 review-repair 后具备真实 Workflow evidence。

### Lightweight core

变更前 `uv sync --dry-run --frozen` 会选择 51 packages；变更后 fresh core 只保留
project 与 PyYAML。`tests/test_agent_first_runtime.py` 在 subprocess import guard 中主动阻止
Camoufox、Playwright、BeautifulSoup、markdownify、httpx 与 pytest import，再运行 discovery
dry-run，避免已安装 optional package 导致 false pass。

### Missing WeChat extra

core-only command 在 browser launch 前经过 `_load_wechat_runtime()` preflight。缺少 optional
dependency 时返回 typed error；CLI 转换为 exit 2 与 install guidance。subprocess test 同时断言
stderr/stdout 不包含 traceback。

## Partial Evidence

### Full WeChat optional install

`uv sync --extra wechat --dry-run --frozen` 能从 lockfile 选择 44 个 optional packages。
真实 install 已启动，但 Playwright/LXML 等下载长期无进展后中止；随后执行 core sync，
当前 `.venv` 已恢复为 2-package default state。

这证明 dependency selection 与 error boundary，但不证明 full 44-package install 已在本机完成。
L5 traceability 保持 `partial`，没有把 dry-run 标为 installed。

### First-run preference write

Skill contract、negative trigger 与 network-free dry-run 已由 test 覆盖；本轮没有在真实 user
config 上执行 preference write，也没有 isolated temp-repository forward test。因此该 Scenario
在 traceability 中保持 `partial`。

## Excluded

- 不运行 live WeChat browser/network fetch。
- 不新增 CLI structured JSON contract。
- 不重做或删除 Web information architecture。
- 既有 legacy datetime Web round-trip gap 与 method-insensitive Node contract probe 不属于本 change。

## Review Decision

PASS with two non-blocking partials：

- `sdd-reviewer` 在读取 direct evidence 后持续超时，Main Agent 按同一
  `validation-rules.md` protocol 完成 fallback verify。
- 第一次 Today forward test 暴露的 dry-run decision defect 已经过
  `review-failed → implementing` 修复，并由第二次 fresh-context test 验证。
- full WeChat optional install 与 preference write 没有被错误升级为 `verified`；
  它们保留在 traceability 与 Known Gaps 中，不阻塞 core Agent-first slice。
- delta 已合并到三个 main Specs，change 状态为 `archived`；`changes/` 只保留 template。
