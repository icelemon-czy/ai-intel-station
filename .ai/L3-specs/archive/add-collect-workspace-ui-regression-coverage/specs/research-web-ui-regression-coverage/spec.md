# Delta Spec: research-web-ui-regression-coverage

> **变更来源**: add-collect-workspace-ui-regression-coverage
> **Delta 类型**: ADDED Requirements（补充到 research-web-workspace 能力域）
> **创建**: 2026-05-27

## ADDED Requirements

### WEB-UI-REGRESS-01 — 导航声明的 section 必须有渲染分支

Every `id` returned by `workspace_sections()` MUST have a corresponding `activeSection === "{id}"` rendering branch in `web/src/App.jsx`. This is a static asset integrity rule.

### WEB-UI-REGRESS-02 — Collect section 渲染存在

App.jsx MUST contain a rendering branch for section id `collect`.

### WEB-UI-REGRESS-03 — 测试必须覆盖完整 section 列表

Tests that exercise the rule in WEB-UI-REGRESS-01 MUST query the live `workspace_sections()` function rather than hardcode a static list, so new sections added in future automatically enter the coverage gate.

## WHEN / THEN Scenarios

### Scenario 1: All navigation sections have rendering branches

```
WHEN  workspace_sections() is called
THEN  for every section with id S in the returned list
      the text 'activeSection === "S"' MUST appear in web/src/App.jsx
```

### Scenario 2: Regression guard catches missing section

```
GIVEN App.jsx contains no branch for section id "collect"
WHEN  the regression test runs
THEN  the test FAILS with a clear message naming the missing section id
```
