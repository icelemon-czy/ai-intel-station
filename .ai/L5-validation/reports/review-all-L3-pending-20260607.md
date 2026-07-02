# Test Review Report — All L3 Pending-Review Changes (2026-06-07)

> 范围：5 个 `pending-review` 状态变更（按创建时间升序）
> 运行者：/review-tests（一次性评审所有 P1 项，给出聚合结论）
> 当前日期：2026-06-07

## 执行结果

- **测试运行**: ❌ 1 个失败（`test_npm_test_in_web_runs_node_test_suite` — `fix-frontend-render-tests-jsdom`），1 个 skip
- **异常标记**: 1 个 skip（`test_library_detail_metadata_order`），1 个 `pass` stub（`test_app_passes_form_props_to_library_section`），1 个 `pytest.skip` 软跳过（`test_library_detail_metadata_order`）
- **审查范围**: 5 个 P1 pending-review 变更

## 主表（每行 = 一个变更的总体结论）

| # | 变更 | 创建时间 | Spec Scenarios | 测试 | 反模式命中 | 结论 |
|:--|:-----|:---------|:---------------|:-----|:-----------|:-----|
| 1 | `fix-frontend-render-tests-jsdom` | 2026-06-02 | 6 | 6 node-tests PASS / 1 python-subprocess FAIL | #2 弱断言、#5 绕开 THEN、#6 条件永真（`assert(true,true)`） | ❌ 打回 |
| 2 | `add-library-safe-markdown-preview` | 2026-06-03 | 7 | 6 PASS / 0 FAIL | #5 绕开 THEN（测 service 函数而非 HTTP 端点）、string-search 而非行为测试、scenarios 6+7 无测试 | ⚠️ 非阻塞 |
| 3 | `fix-frontend-section-switch-preserves-form` | 2026-06-03 | 5 | 2 PASS + 1 deprecated stub（`pass`） | `pass` stub 是反模式 #1（无 assertion）、string-search 而非行为测试、scenarios 1+2+5 无测试 | ⚠️ 非阻塞 |
| 4 | `redesign-library-search-inspection-layout` | 2026-06-03 | 7 | 3 PASS / 1 SKIP / 3 ❌ 缺失 | skip 软跳过未修复（结构变化时静默 skip）、scenarios 2+5+7 无测试 | ❌ 打回（结构性） |
| 5 | `replace-library-file-url-with-safe-local-actions` | 2026-06-03 | 7 | 6 PASS / 1 ❌ 缺失 | scenario 5（clipboard fallback 失败）无测试、所有 string-search | ⚠️ 非阻塞 |

## 覆盖概要

| 变更 | Req | Scenarios | ✅ 有效 | ⚠️ 弱 | 🔴 反模式 | ❌ 缺失 |
|:-----|:----|:----------|:--------|:------|:---------|:-------|
| fix-frontend-render-tests-jsdom | 1 | 6 | 1 (17%) | 1 | 3 | 0 |
| add-library-safe-markdown-preview | 1 | 7 | 5 (71%) | 0 | 1 | 2 |
| fix-frontend-section-switch-preserves-form | 1 | 5 | 1 (20%) | 1 | 1 | 3 |
| redesign-library-search-inspection-layout | 1 | 7 | 3 (43%) | 0 | 0 | 4 |
| replace-library-file-url-with-safe-local-actions | 1 | 7 | 6 (86%) | 0 | 0 | 1 |
| **合计** | **5** | **32** | **16 (50%)** | **2** | **5** | **10** |

## 反模式统计

| 反模式 | 命中次数 | 涉及测试 |
|:-------|:---------|:---------|
| #1 断言缺失 | 1 | `test_app_passes_form_props_to_library_section` (just `pass`) |
| #2 断言太弱 | 1 | `dismissError is exposed as a function and calling it does not throw`（不验证 lastError 是否清空） |
| #5 绕开 Spec THEN | 2 | SSR 测试中 `WithError` 硬编码组件；`read_item_markdown` 测 service 不测 HTTP |
| #6 条件永真 | 1 | `this test file is loaded as part of the suite`（`assert.equal(true, true)`） |
| skip 软跳过 | 1 | `test_library_detail_metadata_order`（结构变化时 pytest.skip 静默通过） |

## 失败 / 阻塞项

| 类型 | 描述 | 位置 | 建议 |
|:-----|:-----|:-----|:-----|
| ❌ 测试失败 | 硬编码 `pass 24 / 25 / 26` 断言过窄 | `tests/test_web_workspace.py:1484` | 改为 `pass >= 24` 或校验 `(pass X)` 正则抽取后再 `>= 24` |
| ❌ 软跳过 | `pytest.skip` 在结构变化时静默通过 | `tests/test_web_workspace.py:2002` | 改为 `xfail(reason=...)` + 计划修复 |
| ❌ Stub 占位 | `test_app_passes_form_props_to_library_section` 仅 `pass` | `tests/test_web_workspace.py:1598-1601` | 删除（已 deprecated 注释） |

## 缺失 Scenario（spec 写了但没测）

| 变更 | Scenario | 描述 |
|:-----|:---------|:-----|
| fix-frontend-section-switch-preserves-form | #1 user-typed keyword survives | 没有真实输入/重渲染测试，只有 source-level 字符串扫描 |
| fix-frontend-section-switch-preserves-form | #2 user-selected sources survive | 同上 |
| fix-frontend-section-switch-preserves-form | #5 other sections unaffected | 完全未测 |
| add-library-safe-markdown-preview | #6 detail panel shows error for unreadable | 缺失 |
| add-library-safe-markdown-preview | #7 preview does not modify state | 缺失 |
| redesign-library-search-inspection-layout | #2 results list dominant width | 缺失（需 browser/CSS 渲染） |
| redesign-library-search-inspection-layout | #5 row card emphasizes scan fields | 缺失 |
| redesign-library-search-inspection-layout | #7 legacy 3-column class removed | 仅检查 `library-layout` 不在 section root 字符串中，未遍历整个 styles.css |
| replace-library-file-url-with-safe-local-actions | #5 clipboard API failure fallback | 完全未测 |

## 结论（必填）

- [ ] ❌ 打回（`fix-frontend-render-tests-jsdom`、`redesign-library-search-inspection-layout`）
- [x] ⚠️ 有缺口但非阻塞（`add-library-safe-markdown-preview`、`fix-frontend-section-switch-preserves-form`、`replace-library-file-url-with-safe-local-actions`）

### 打回原因

1. ❌ `fix-frontend-render-tests-jsdom` — `test_npm_test_in_web_runs_node_test_suite` 失败（硬编码 24/25/26 期望，实际 pass 46）→ `/fix-bug` Step 3B 改为 ≥ 24 范围断言
2. ❌ `redesign-library-search-inspection-layout` — `test_library_detail_metadata_order` 静默 skip → 改为 xfail + 修结构检测

### 已知缺口（不阻塞归档）

- 50% Scenario 覆盖：3/5 变更的核心 Scenario 只有字符串扫描测试，没有真实行为/渲染验证
- 5 个反模式命中集中在 SSR + service-level 测试，需补 React 渲染测试或 jsdom 路径
- 1 个 deprecated stub 应在下次清理

## 关于用户关切："briefing / collect workspace 感觉没有多少改善"

我额外查看了两个 `implementing` 状态的变更，它们直接对应这两个 workspace 的实际改进：

1. **`fix-web-dashboard-and-briefing-css-layout`**（implementing，2026-06-07）— 已落 CSS 修复（hero-card 网格、metric-card box-shadow、app-shell safe-area、briefing sticky action-row），现在在 backfill spec/test/traceability（proposal 明确写"代码: 不动"）
2. **`fix-web-collect-workspace-layout`**（implementing，2026-06-07，嵌套 depth 2）— CSS 修改中（collect 上下文下的 page-purpose-card 对比度、source-switch border alpha、collect-sidecar 窄屏边距），同样在 backfill 测试

**结论**：用户感知"没有多少改善"是**准确的**：
- 实际 CSS 改进已经在最新 commit `3737de0 fix(web): backfill CSS spec+tests + 3 new briefing fixes` 里
- 但**当前 5 个 pending-review 变更都不涉及 briefing/collect 布局**——这 5 个全是 Library（markdown preview、section switch、layout redesign、file:// 替换）
- briefing/collect 的 CSS 修复在两个 `implementing` 变更里走的是"**CSS 已落位、追溯式 backfill**"路径，proposal 自己也承认"全部跳过了 /fix-bug 纪律"

因此：用户感知的"briefing/collect 没改善"很可能是因为**刚 commit 完 CSS 修复但用户尚未刷新页面 / 未触发相应 action**，或者**已经看到效果但认为幅度小**。建议：

1. 完成两个 implementing 变更的 spec+test backfill（不要让它们停在 implementing）
2. 让 CSS 修复可见——重启 dev server、清除 browser cache 后再走一遍 collect/briefing 流程
3. 在用户已批准 `clarify-briefing-generation-flow` / `standardize-collect-run-result-explanations`（2026-06-01）的基础上，告诉他后续还有 `fix-web-dashboard-and-briefing-css-layout` 和 `fix-web-collect-workspace-layout` 在 implementing，让他有"马上会改善"的预期
