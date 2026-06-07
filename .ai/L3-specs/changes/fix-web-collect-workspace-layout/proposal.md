# Fix: Web Collect Workspace Layout, Visibility, And Contrast

> **状态**: implementing
> **创建**: 2026-06-07
> **父变更** (parent-change): `fix-web-dashboard-and-briefing-css-layout`
> **嵌套深度** (depth): 2

## Why

Collect Workspace (`web/src/App.jsx::CollectSection`) 暴露 4 个前端显示问题,影响用户的核心"输入 → Run now"流程的可达性、关键说明文字的可见性、视觉对比度与右侧安全区:

1. **核心表单 (Search Query / Max Results / Run now) 被挤出首屏** — collect-panel 内首屏可见的是 "FIRST RUN" 提示框 + 数据源切换按钮,真正可输入的 `<input>` 字段和提交按钮在 `collect-panel` 堆叠 6 个子区块(title / h2 / supporting / empty-state-panel / source-list / purpose-card)之后才出现,需要滚动才能触达
2. **PagePurposeCard 的 Reads / Produces 文字不可见** — collect-layout 是 2 列 grid,`PagePurposeCard` 作为直接子元素 auto-place 到第 1 列第 1 行(列宽 320–420px);但其内部 `.page-purpose-grid` 用了 `repeat(auto-fit, minmax(220px, 1fr))`,在窄列下挤压,加之渐变背景 `linear-gradient(135deg, var(--accent-soft), rgba(15, 118, 110, 0.04))` 与文字色对比度较弱,Reads / Produces 子项视觉上"消失"
3. **右侧悬浮按钮依然压住 collect-sidecar 边界** — 上一轮已在 `.app-shell` 加 `padding-right: 80px`,但 collect-sidecar 是 `grid-template-columns: minmax(320px, 420px) minmax(0, 1fr)` 的右列,如果 .app-shell 的 80px 在 1024px 以下被还原,collect 在窄屏上仍会被压;需明确"所有 section 都继承 app-shell 右侧安全区"的契约
4. **Source switch 未选中态对比度过低** — `.source-switch` 默认 `border: 1px solid var(--line)`,`var(--line)` 是 `rgba(21, 34, 36, 0.12)` (12% 黑色),在浅米色 panel 背景上几乎不可见,违反 WCAG 1.4.11 (Non-text Contrast)

## What Changes

- **Spec**: 在 `specs/research-web-workspace/spec.md` 新增 4 个 Requirement 覆盖:
  - Collect Form Stays Above The Fold
  - PagePurposeCard Displays Reads And Produces With Sufficient Contrast
  - Collect Layout Inherits App Shell Right Safe-Area
  - Source Switch Buttons Meet Accessibility Contrast
- **测试**: 新增 `web/test/collectLayout.test.mjs` — 沿用 `dashboardLayout.test.mjs` 的 CSS schema 静态断言风格,覆盖:
  - `.collect-layout .empty-state-panel` (collect 上下文下) 使用更紧凑的 padding/gap
  - `.collect-layout .empty-state-panel` 在 collect 上下文下可被 `<details>` 折叠(由 JSX 配合,本变更只断 CSS 钩子)
  - `.page-purpose-card` 显式声明 `color:` 属性,确保子项 `<dt>` / `<dd>` 在渐变背景上有足够对比度
  - `.collect-sidecar` 与 `.collect-panel` 在 1024px 以下保留水平边距,不被 .app-shell 的窄屏还原影响
  - `.source-switch` 默认 `border-color` 的 alpha ≥ 0.30 (WCAG 1.4.11 视觉估算)
  - `.source-switch.active` 不被新规则覆盖(选中态对比度仍保留)
- **代码**: 修复 `web/src/styles.css`:
  - 压缩 `.collect-layout .empty-state-panel` 的 padding / font-size,挂上 `<details>` 友好的 `summary` 样式钩子(JSX 后续单独变更)
  - 增强 `.page-purpose-card` 的 `color:` 声明 + `.page-purpose-grid` 在 collect 上下文下改为单列
  - 加固 `.collect-sidecar` / `.collect-panel` 的窄屏边距
  - 提升 `.source-switch` 默认 border 透明度
- **追溯**: 更新 `.ai/L5-validation/traceability/research-web-workspace.md` 把 4 个新 Requirement 标记为 ✅ verified

## Alternatives Considered

1. **把 FIRST RUN 提示框改成 `<details>` 折叠并默认关闭** — 涉及 JSX 变更,本变更只断 CSS 钩子(`.collect-layout .empty-state-panel details > summary`),JSX 改造留作后续单独立项(避免在 fix-bug 循环中混 JSX 改动)
2. **把 PagePurposeCard 移到 sidecar 顶部** — 改变信息架构,需要 UX 决策,超出 fix-bug 范围
3. **把 collect 拆成 3 列(说明 / 表单 / sidecar)** — 大改布局,留作后续 explore

## Capabilities Affected

### Modified Capabilities

- `research-web-workspace`: 补 spec 覆盖 Collect Workspace 的可达性 / 可见性 / 对比度 / 响应式契约

## Impact

- **Spec**: `specs/research-web-workspace/spec.md` 新增 4 个 Requirement / 12 个 Scenario
- **Test**: `web/test/collectLayout.test.mjs` (新), 6 个 test case
- **CSS**: `web/src/styles.css` 净增 ~40 行(新增 `.collect-layout` 上下文规则 + 提升 `.source-switch` 对比度)
- **JSX**: 不动(本轮纯 CSS + spec + test)
- **Traceability**: `.ai/L5-validation/traceability/research-web-workspace.md` 新增 4 行

## 状态转移日志

- `2026-06-07 00:00` — [drafting] → [implementing] by /fix-bug | 原因: 用户明确要求按 /fix-bug 流程依次处理 Collect 4 个 bug
