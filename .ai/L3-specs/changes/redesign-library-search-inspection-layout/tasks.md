# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试。

- [x] 1.1 top filter bar holds all search controls (Python source-level)
- [x] 1.2 results list occupies the dominant width
- [x] 1.3 page-purpose / search-scope copy is demoted
- [x] 1.4 detail panel groups metadata in a clear order
- [x] 1.5 row card emphasizes scan fields
- [x] 1.6 pagination stays in the result panel
- [x] 1.7 legacy three-column class names are not used

## 2. Frontend (App.jsx + styles.css)

- [x] 2.1 `LibrarySection` 把搜索表单重写为顶部 `library-filter-bar` 横排 (keyword / sources / since / until / search / count)
- [x] 2.2 主区域改为 `library-workspace` 两栏 (左 result / 右 detail)
- [x] 2.3 `PagePurposeCard` + `library-scope-note` 改为 eyebrow / collapsible，不再占满一行
- [x] 2.4 `detail-panel` 信息层级按 title → summary → metadata → path → actions 排序
- [x] 2.5 `result-card` 紧凑化（≤4 行）
- [x] 2.6 删 `library-layout` 旧 class（或替换为新的两栏 class）

## 3. Wire it up

- [x] 3.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 3.2 跑 `web/test/*.test.mjs` 全绿
- [x] 3.3 端到端：浏览器打开 Library，filter bar 在顶、result 列表宽、详情在右

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
