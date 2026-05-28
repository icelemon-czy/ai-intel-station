# 当前会话状态

> ⚡ 每次对话必读 + 对话结束时更新
> 这是 AI 的短期工作记忆，记录"上一步做到哪了、下一步该做什么"。

## 最后更新

- **时间**: 2026-05-29
- **对话主题**: 分析 Web Library / Collect 新反馈，并拆成新的 draft change proposals

## 当前工作焦点

**当前在做**: 将最新的 5 个 Web 反馈拆成独立变更，供后续逐个 `/new-change` 确认

- `.ai/L3-specs/changes/add-library-result-pagination-and-position-cues/` — `drafting`
- `.ai/L3-specs/changes/expand-library-item-detail-with-inline-preview-and-local-open/` — `drafting`
- `.ai/L3-specs/changes/align-web-source-labels-between-library-and-collect/` — `drafting`

说明：
- 用户反馈“看不出当前正在看哪个 result”已命中现有 `.ai/L3-specs/changes/add-library-selection-state-and-active-styling/`，本轮不重复建单
- 用户质疑“web 里没用 React”经代码核对后不成立；这是认知澄清，不单独立项

**已完成上一轮 TDD 循环，等待 /review-tests**

- `.ai/L3-specs/changes/align-web-collect-with-local-output-truth/` — `pending-review` ✅
- `.ai/L3-specs/changes/add-collect-workspace-ui-regression-coverage/` — `pending-review` ✅

- `.ai/L3-specs/changes/standardize-web-collect-result-summaries/` — `drafting`（待后续）
- `.ai/L3-specs/changes/refresh-web-workspace-after-collect-run/` — `drafting`（待后续）

- `.ai/L3-specs/changes/clarify-web-navigation-and-page-purpose/` — `drafting`
- `.ai/L3-specs/changes/add-library-selection-state-and-active-styling/` — `drafting`
- `.ai/L3-specs/changes/add-first-run-empty-states-and-onboarding/` — `drafting`
- `.ai/L3-specs/changes/upgrade-dashboard-from-overview-to-action-center/` — `drafting`
- `.ai/L3-specs/changes/add-collect-workspace-shell/` — `drafting`
- `.ai/L3-specs/changes/add-wechat-url-collection-form/` — `drafting`
- `.ai/L3-specs/changes/add-github-and-papers-collection-forms/` — `drafting`
- `.ai/L3-specs/changes/add-local-job-runner-and-job-history/` — `drafting`
- `.ai/L3-specs/changes/add-scheduled-collection-and-refresh-policies/` — `drafting`
- `.ai/L3-specs/changes/add-runtime-diagnostics-and-preflight-checks/` — `drafting`

- `.ai/L3-specs/changes/add-react-web-workspace-mvp/` — `pending-review`
- `.ai/L3-specs/changes/add-research-item/` — `pending-review`
- `.ai/L3-specs/archive/add-research-operator-surface/` — `archived` ✅

**下一步**: 执行 `/review-tests align-web-collect-with-local-output-truth` 或 `/review-tests add-collect-workspace-ui-regression-coverage`

## 已完成（本轮）

- [x] 分析 5 条新反馈与当前实现的映射关系，确认：分页缺失、详情过薄、来源标签漂移是新的独立需求；结果选中态已有 existing change；React 技术栈已存在
- [x] 新增 3 个 draft proposal：`add-library-result-pagination-and-position-cues`、`expand-library-item-detail-with-inline-preview-and-local-open`、`align-web-source-labels-between-library-and-collect`
- [x] 选定 2 个最有价值的 collect 闭环提案进入 TDD 循环：`align-web-collect-with-local-output-truth` + `add-collect-workspace-ui-regression-coverage`
- [x] 为两个提案创建 delta spec（`specs/*/spec.md`）和 `tasks.md`
- [x] 更新 `tests/test_web_workspace.py`：
  - 新增 3 个 WEB-COLLECT-PERSIST 测试（确认对 output_root 的正确传递）
  - 新增 1 个 WEB-UI-REGRESS 测试（确认所有 navigation section 都有 React 渲染分支）
  - 更新 `test_run_collect_papers` 增加 `save_papers` mock 断言
  - 更新 `test_run_collect_wechat` 改为 async mock
- [x] 实现 `workspace_web/service.py` — `run_collect()` 增加 `output_root: Path | None = None` 参数，修复 3 个 handler（GitHub 写 `/tmp/output` → `root/github`；papers 补 `save_papers()` 落盘调用；WeChat 改用 `asyncio.run()` 正确执行 async）
- [x] 实现 `workspace_web/server.py` — POST `/api/collect/run` 透传 `output_root`
- [x] 运行测试：`tests/test_web_workspace.py` 29/29 通过，全套 60/60（除预存在 `markdownify` 缺依赖外）
- [x] 将两个提案推进到 `pending-review`

- [x] 诊断 Web 二期 proposal 与当前实现的偏差，确认 `workspace_web` 已有 collect 导航与 API，但 `web/src/App.jsx` 缺少 `collect` section 的实际渲染
- [x] 在 React 前端补齐 Collect Workspace 页面壳层，接入 `/api/collect/sources`、`/api/collect/form/:source`、`/api/collect/run`
- [x] 在 Collect Workspace 明确标注当前只支持手动 Run now；jobs history、schedule 和 refresh policy 尚未进入前端显示
- [x] 运行 `npm --prefix web run build`，前端构建通过，新的 collect 页面已产出到 `workspace_web/static/`

- [x] 将 Web 二期交互需求拆成 10 个独立 draft proposal，覆盖导航命名、Library 选中态、空状态、Dashboard 升级、Collect Workspace、WeChat 表单、GitHub/papers 表单、jobs、schedule、diagnostics
- [x] 为每个 proposal 增加建议优先级、建议顺序和依赖关系，便于用户 review 后挑选真正要执行的 `/new-change`
- [x] 更新 session 状态，使当前焦点从 review 队列临时切到“proposal review”阶段

- [x] `/review-tests add-research-operator-surface` — 全量场景 7/7 覆盖，反模式 0 命中，测试全绿 ✅
- [x] 写入审查报告 `.ai/L5-validation/reports/review-add-research-operator-surface-20260525.md`
- [x] 将 `add-research-operator-surface` 状态从 `pending-review` 升为 `approved`
- [x] 执行 `/archive-change add-research-operator-surface` — delta spec 合并、新建 `specs/research-operations/spec.md`、变更归档至 `archive/add-research-operator-surface/`

- [x] 为 `add-react-web-workspace-mvp` 编写 8 个 Web MVP 场景测试，并确认红灯失败点集中在 `workspace_web` 模块与 `research web` 入口
- [x] 实现 `workspace_web/service.py` 本地桥接层，覆盖 Dashboard、Library、Briefing 预览与保存
- [x] 为统一入口新增 `web` 子命令，并实现 `workspace_web/server.py` 本地静态资源 + API 服务
- [x] 新建 `web/` React + Vite 前端源，并完成本地 build 到 `workspace_web/static/`
- [x] 更新 `README.md`、`overview.md` 与 `features/research-web-workspace/README.md`，对齐新的本地 Web 能力
- [x] 更新 `traceability/research-web-workspace.md` 与 `traceability/system.md`，标记新场景为 verified
- [x] 将 `add-react-web-workspace-mvp` 状态从 `implementing` 推进到 `pending-review`

- [x] 通过 `/continue-change 1` 选择 `add-react-web-workspace-mvp` 继续开发，并按 proposal 默认边界接受第一期范围
- [x] 将 `add-react-web-workspace-mvp` 状态从 `drafting` 推进到 `implementing`
- [x] 为 `research-web-workspace` 新增 delta spec，覆盖 Dashboard / Library / Briefing Workspace / MVP scope guard
- [x] 为 `system` 新增 delta spec，约束 CLI 与 Web 共用本地 archive truth，并为 Web 补 documented entrypoint 要求
- [x] 生成 `add-react-web-workspace-mvp/tasks.md`，将接续点推进到 Tests 组

- [x] 按 `/new-change` 读取 workflow playbook、system spec、proposal template 与当前 changes 状态
- [x] 回溯旧变更中"Web/TUI 不在第一阶段"的历史决策，确认本次是新的独立 change，而不是对旧 proposal 的补丁
- [x] 起草 `.ai/L3-specs/changes/add-react-web-workspace-mvp/proposal.md`，将第一期范围收敛为 Dashboard / Library / Briefing Workspace
- [x] 生成待确认的业务问题，准备在用户确认后进入 delta spec 与 tasks 阶段

- [x] 按 `/review-tests` 选择队列首个目标 `add-research-item`
- [x] 逐 Scenario 对照 delta spec 与 `tests/test_research_item.py`，发现 runtime sidecar 持久化场景缺少直接测试
- [x] 运行相关测试：`python3 -m pytest tests/test_research_item.py`，结果 `4 passed`
- [x] 写入审查报告 `.ai/L5-validation/reports/review-add-research-item-20260519.md`
- [x] 将 `add-research-item` 状态从 `pending-review` 回流为 `review-failed`
- [x] 执行 `/fix-bug add-research-item`，补齐 runtime sidecar 持久化测试、normalization 断言和 backfill preservation 断言
- [x] 更新 GitHub / papers / WeChat / archive-output traceability，标记对应 sidecar 场景为 verified
- [x] 将 `add-research-item` 状态从 `review-failed` 推回 `pending-review`
- [x] 新建根级 `research` 包和 `research` script，统一 collect / query / briefing / backfill 表面
- [x] 删除旧 runtime wrapper 文件：`research_item.py`、`github-tools/fetch_github.py`、`papers-tools/fetch_papers.py`、`wechat-article-to-markdown/wechat_article_to_markdown.py`、`wechat-article-to-markdown/main.py`
- [x] 将 WeChat 测试迁入根级 `tests/test_wechat_collect.py` 与 `tests/test_wechat_e2e_live.py`
- [x] 清理 `.ai` 活跃文档中的 patch artifact，并移除 `.ai/.github` 重复 workflow tree
- [x] 更新 `.ai` 导航、feature README、traceability、session、AGENTS、CLAUDE 到新的业务结构
- [x] 将来源参考资料集中到 `tools/`，不再让旧 tool 目录占据 repo root 主表面
- [x] 为根级 `pytest` 注册 `e2e` marker，清除测试 warning

## 测试状态

- ✅ `/opt/homebrew/opt/python@3.10/bin/python3.10 -m pytest tests/test_restructure_research_architecture.py`
  - 结果：`8 passed`
- ✅ `python3 -m pytest tests/test_web_workspace.py`
  - 结果：`8 passed`
- ✅ `python3 -m pytest tests/test_web_workspace.py tests/test_restructure_research_architecture.py`
  - 结果：`16 passed`
- ✅ `npm --prefix web install --no-audit --no-fund --loglevel=error && npm --prefix web run build`
  - 结果：React / Vite 构建成功，静态资源输出到 `workspace_web/static/`
- ✅ `python3 -m research web` + `curl http://127.0.0.1:4173/` + `curl http://127.0.0.1:4173/api/navigation` + `curl http://127.0.0.1:4173/api/dashboard`
  - 结果：首页、导航 API 与 Dashboard API 均返回成功
- ✅ `python3 -m pytest tests/test_research_item.py`
  - 结果：`8 passed`
- ✅ `python3 -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py`
  - 结果：`16 passed`
- ⚠️ `uv run --with pytest python -m pytest tests/test_research_item.py`
  - 结果：sandbox 无法访问 `~/.cache/uv`，提权自动审批超时；本轮用 `python3` 完成目标文件验证
- ✅ `uv run --with pytest python -m pytest tests/test_wechat_collect.py`
- ✅ `uv run --with pytest python -m pytest tests/test_ai_context_alignment.py`
- ✅ `uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_ai_context_alignment.py tests/test_wechat_collect.py tests/test_wechat_e2e_live.py`
  - 结果：`28 passed, 1 skipped`

## 阻塞 / 待确认

- 这 10 个 proposal 目前都处于 `drafting`；需要用户 review 后决定哪些进入正式 `/new-change` 确认流程
- Twitter 仍未进入系统边界；当前只保留 `tools/twitter/README.md` 作为占位说明
- GitHub / papers 仍缺真实外部依赖 smoke 或更强自动化测试
- WeChat live e2e 仍为 opt-in；未设置 `WECHAT_E2E_URLS` 时应继续 skip

## 上下文备注

- 当前对外运行入口只保留 `research/cli.py`
- 来源参考资料现在集中在 `tools/`，不再占据 repo root 主表面，也不再是 runtime source of truth
- `output/` 仍分为原始归档层和 `output/briefing/` 派生阅读层

---

## 会话历史摘要

| 日期 | 主题 | 成果 |
| --- | --- | --- |
| 2026-05-09 | `.ai` 基建补齐 | 已将 L1 从模板替换为 research 仓库的真实导航与入口映射 |
| 2026-05-10 | operator surface 迁移 | 已完成统一入口、旧 wrapper 移除、根级测试迁移与 `.ai` 收口 |
