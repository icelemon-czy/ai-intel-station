# 当前会话状态

> ⚡ 每次对话必读 + 对话结束时更新
> 这是 AI 的短期工作记忆，记录“上一步做到哪了、下一步该做什么”。

## 最后更新

- **时间**: 2026-05-10
- **对话主题**: 完成统一 `research` operator surface、移除旧 runtime wrapper、将旧来源参考资料收口到 `tools/`

## 当前工作焦点

**正在做**: 以下 3 个 change 已完成实现并进入 `pending-review`

- `.ai/L3-specs/changes/add-research-operator-surface/`
- `.ai/L3-specs/changes/separate-legacy-compatibility-layer/`
- `.ai/L3-specs/changes/align-ai-context-with-business-architecture/`

**涉及文件**:

- `research/` — 统一 operator surface（collect / query / briefing / backfill）
- `collect/` — GitHub / papers / WeChat 真实收集实现
- `library/` — `ResearchItem`、sidecar 扫描、历史 backfill、本地查询
- `briefing/` / `publish/` — 派生简报与 `output/briefing/` 落盘
- `tests/` — 根级回归测试，含 WeChat 单测和 opt-in live e2e
- `.ai/L1-codebase-map/*` / `.ai/L5-validation/*` — 导航、traceability、validation 规则已同步

## 已完成（本轮）

- [x] 新建根级 `research` 包和 `research` script，统一 collect / query / briefing / backfill 表面
- [x] 删除旧 runtime wrapper 文件：`research_item.py`、`github-tools/fetch_github.py`、`papers-tools/fetch_papers.py`、`wechat-article-to-markdown/wechat_article_to_markdown.py`、`wechat-article-to-markdown/main.py`
- [x] 将 WeChat 测试迁入根级 `tests/test_wechat_collect.py` 与 `tests/test_wechat_e2e_live.py`
- [x] 清理 `.ai` 活跃文档中的 patch artifact，并移除 `.ai/.github` 重复 workflow tree
- [x] 更新 `.ai` 导航、feature README、traceability、session、AGENTS、CLAUDE 到新的业务结构
- [x] 将来源参考资料集中到 `tools/`，不再让旧 tool 目录占据 repo root 主表面
- [x] 为根级 `pytest` 注册 `e2e` marker，清除测试 warning

## 下一步具体动作

1. [ ] 执行 `/review-tests`，优先审查这 3 个 change 的 operator surface、wrapper removal、`.ai` 对齐测试是否足够
2. [ ] 如 reviewer 需要更强证据，再补真实 `gh` / arXiv smoke 或 WeChat live 运行记录
3. [ ] review 通过后执行 `/archive-change`，把 delta spec 合并回主 spec

## 测试状态

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
