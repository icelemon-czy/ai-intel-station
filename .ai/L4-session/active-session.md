# 当前会话状态

> ⚡ 每次对话必读 + 对话结束时更新
> 这是 AI 的短期工作记忆，记录“上一步做到哪了、下一步该做什么”。

## 最后更新

- **时间**: 2026-05-25
- **对话主题**: 完成 `add-react-web-workspace-mvp` 的实现、验证与 pending-review 收尾

## 当前工作焦点

**正在做**: `add-react-web-workspace-mvp` 已完成实现并进入 `pending-review`；当前队列共有 6 个 pending-review change

- `.ai/L3-specs/changes/add-react-web-workspace-mvp/` — `pending-review`

- `.ai/L3-specs/changes/add-research-item/` — `pending-review`
- `.ai/L3-specs/changes/add-research-operator-surface/`
- `.ai/L3-specs/changes/separate-legacy-compatibility-layer/`
- `.ai/L3-specs/changes/align-ai-context-with-business-architecture/`
- `.ai/L3-specs/changes/restructure-research-architecture/`

**涉及文件**:

- `research/` — 统一 operator surface（collect / query / briefing / backfill）
- `collect/` — GitHub / papers / WeChat 真实收集实现
- `library/` — `ResearchItem`、sidecar 扫描、历史 backfill、本地查询
- `briefing/` / `publish/` — 派生简报与 `output/briefing/` 落盘
- `tests/` — 根级回归测试，含 WeChat 单测和 opt-in live e2e
- `.ai/L1-codebase-map/*` / `.ai/L5-validation/*` — 导航、traceability、validation 规则已同步

## 已完成（本轮）

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
- [x] 回溯旧变更中“Web/TUI 不在第一阶段”的历史决策，确认本次是新的独立 change，而不是对旧 proposal 的补丁
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

## 下一步具体动作

1. [ ] 执行 `/review-tests add-react-web-workspace-mvp`，审查 Web MVP 测试是否覆盖到位，尤其是 live UI 与 startup path 风险
2. [ ] 审查通过后，回到 `/review-tests add-research-item` 队列，继续清理已有 pending-review 变更
3. [ ] 如 reviewer 需要更强证据，可补浏览器级 smoke 或 `research web` 的启动脚本包装

## 测试状态

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
- ✅ `PYTHONPATH=.venv/lib/python3.10/site-packages python3 -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_wechat_collect.py`
  - 结果：`30 passed`
- ✅ `PYTHONPATH=.venv/lib/python3.10/site-packages python3 -m pytest`
  - 结果：`32 passed, 1 skipped`
- ⚠️ `uv run --with pytest python -m pytest tests/test_research_item.py`
  - 结果：sandbox 无法访问 `~/.cache/uv`，提权自动审批超时；本轮用 `python3` 完成目标文件验证
- ✅ `uv run --with pytest python -m pytest tests/test_wechat_collect.py`
- ✅ `uv run --with pytest python -m pytest tests/test_ai_context_alignment.py`
- ✅ `uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_ai_context_alignment.py tests/test_wechat_collect.py tests/test_wechat_e2e_live.py`
  - 结果：`28 passed, 1 skipped`

## 阻塞 / 待确认

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
