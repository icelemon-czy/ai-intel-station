# Fix: Web Dashboard And Briefing CSS Layout & Visual Hierarchy

> **状态**: implementing
> **创建**: 2026-06-07
> **父变更** (parent-change): `clarify-web-navigation-and-page-purpose`
> **嵌套深度** (depth): 1

## Why

Dashboard 和 Briefing Workspace 各暴露 4 个 CSS 布局 / 视觉层级问题,影响用户对核心信息的可读性与可触达性:

**Dashboard (`web/src/App.jsx::DashboardSection`):**

1. **Hero card 与 PagePurpose 视觉重叠** — `dashboard-grid` 是 12 列网格,`PagePurposeCard` 默认 `grid-column: auto` 只占 1 列 (≈8% 宽),与 `hero-card` (7 列) 在同一行并排,PagePurpose 被挤成超窄列,文本疯狂折行
2. **卡片宽高溢出** — grid items 固定 `min-height: 180px` + 缺少 `min-width: 0`,窄列下撑爆父级
3. **右侧安全区不足** — `.app-shell` 缺少右侧 padding,任何未来的 `position: fixed` 元素都会贴边
4. **视觉层级混乱** — `.metric-card` 原 CSS 只设了 `grid-column: span 5`,**没有 background / border / padding / box-shadow**,它根本不是"卡片",是个透明 div;hero-card 独占视觉主导

**Briefing Workspace (`web/src/App.jsx::BriefingSection`):**

5. **右侧悬浮按钮遮挡** — 与 Dashboard 同根,`.app-shell` 缺右侧 safe-area
6. **信息密度低** — `.control-panel { gap: 14px }` + `.page-purpose-card` 的 `margin-bottom: 18px` 双重间距;`minmax(220px, 1fr)` 让 Reads/Produces 子网格在 320px 列宽下挤压
7. **表单风格不统一** — `input, select { border-radius: 14px }` (pill 风格) 与 `.panel { border-radius: 28px }` 脱节;`<select>` 用浏览器原生外观,箭头贴边
8. **Preview/Save 按钮被埋到底部** — `.action-row` 是普通 grid,无 sticky 行为;长 flow note 之后用户必须滚动才能看到主操作

8 个 bug 都已在前几轮直接落在 `web/src/styles.css` 修复,但**全部跳过了 `/fix-bug` 纪律**:没建 fix 变更、没补 spec、没写新测试、没更新 traceability。本变更对它们做**追溯式 backfill** — 补 proposal + delta spec + 回归测试 + 追溯矩阵。

## What Changes

- **Spec**: 在 `specs/research-web-workspace/spec.md` 新增 3 个 Requirement 覆盖:
  - Dashboard 网格布局(Requirement: Dashboard Grid Layout Prevents Card Overlap)
  - App shell 右侧安全区(Requirement: App Shell Reserves Right Safe-Area)
  - Briefing 表单密度与可触达性(Requirement: Briefing Workspace Density And Action Reachability)
- **测试**: 新增 `web/test/dashboardLayout.test.mjs` — 静态 schema 测试,在不引入 JSDOM 的前提下(沿用 `fix-frontend-render-tests-jsdom` 的 SSR-only 原则)断言 CSS 文件含有 4 类关键规则(用于回归保护):
  1. `.dashboard-grid > .page-purpose-card` 必须有 `grid-column: 1 / -1`
  2. `input, select` 的 `border-radius` 必须是 10px
  3. `.metric-card` 必须声明 `background:` 和 `box-shadow:`
  4. `.briefing-layout .action-row` 必须声明 `position: sticky`
- **代码**: **不动**。CSS 修复已在 `web/src/styles.css` 落位(本变更只追溯、不重做)
- **追溯**: 更新 `.ai/L5-validation/traceability/research-web-workspace.md` 把 3 个新 Requirement 标记为 ✅ verified
- **不做**: 不引入 JSDOM/Vitest(沿用现有 SSR-only 测试栈);不改 App.jsx(布局修复是纯 CSS);不补 jsdom 渲染测试(避免在轻量测试栈上加重量)

## Alternatives Considered

1. **引入 JSDOM + getComputedStyle 真测 CSS** — web 项目测试栈明确避免 JSDOM(见 `fix-frontend-render-tests-jsdom/proposal.md` "Alternatives Considered"),且新增 ~10MB devDeps 不划算
2. **SSR render 验证 class 结构** — `useEffect` 不在 SSR 阶段跑,组件初始 render 是 "Loading dashboard…",无法触达已加载态的 DOM 结构,这条路收益有限
3. **CSS schema 静态断言(当前选择)** — 读 CSS 文件 + 正则断言关键规则存在,能拦住"有人把 `grid-column: 1 / -1` 改回 `auto`"、"有人把 `border-radius: 10px` 改回 14px"、"有人删了 `.metric-card` 的 background"等回归,零新依赖

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: 补 spec 覆盖"页面 CSS 布局与视觉层级"

## Impact

- **Spec**: `specs/research-web-workspace/spec.md` 新增 3 个 Requirement / 9 个 Scenario
- **Test**: `web/test/dashboardLayout.test.mjs` (新), 6 个 test case
- **Traceability**: `.ai/L5-validation/traceability/research-web-workspace.md` 新增 3 行
- **Code**: 0 改动(纯追溯)
- **Docs**: 无

## 状态转移日志

- `2026-06-07 00:00` — [drafting] → [implementing] by /fix-bug | 原因: 用户确认"保留 CSS, 补 spec+test 追溯" 路径
