# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会把这些新增的 Requirement 合并到主 spec 中。

## ADDED Requirements

### Requirement: Collect Form Stays Above The Fold

The Collect Workspace MUST lay out its left column (`<form class="collect-panel">`) so that the **first text input** and the **Run now** submit button are both visible within the initial viewport (1024×768 desktop) without scrolling. The vertical space wasted by the "FIRST RUN" empty-state guidance MUST be compressible — either via tighter typography inside collect, or via a CSS hook (e.g. wrapping the guidance in a `<details>` element styled to be collapsed by default).

#### Scenario: Empty-state panel uses compact padding inside collect

- **WHEN** `.empty-state-panel` is rendered inside `.collect-layout` (i.e. as a direct or nested child of the collect form)
- **THEN** the `.collect-layout .empty-state-panel` CSS rule MUST set `padding` to at most `12px` (compact mode)
- **AND** the rule MUST set `font-size` on inner `<li>` and `<p>` elements to at most `13px` so the panel does not dominate the initial viewport

#### Scenario: Empty-state panel supports a collapsible `<details>` summary

- **WHEN** the FIRST RUN guidance is wrapped in a `<details>` element inside `.collect-layout`
- **THEN** the `.collect-layout .empty-state-panel details > summary` rule MUST render as a clickable header with a visible chevron
- **AND** the body content of the `<details>` MUST be hidden when the details is closed (default browser `<details>` behavior)

#### Scenario: Action row uses the same sticky footer as briefing

- **WHEN** the collect panel renders its `.action-row` (containing "Run now" + execution-mode note)
- **THEN** the rule MUST keep the action row within the form's vertical flow (not sticky-pinned) — the Run now button is the only primary action and must always be reachable, but it should not float over the FIRST RUN guidance
- **AND** the action row MUST use the same compact 10px gap as `.briefing-layout .control-panel`

### Requirement: PagePurposeCard Displays Reads And Produces With Sufficient Contrast

The `PagePurposeCard` (rendered inside `.collect-layout`, `.briefing-layout`, etc.) MUST display the `Reads` and `Produces` fields with sufficient contrast against its gradient background. The `Reads` / `Produces` sub-grid MUST adapt to a single column when the parent column is narrower than 360px (collect and briefing left columns).

#### Scenario: page-purpose-card declares a base text color

- **WHEN** any `.page-purpose-card` is rendered (in any section)
- **THEN** the `.page-purpose-card` CSS rule MUST declare a `color:` property (not rely on inheritance) so child `<dt>` / `<dd>` default to a known high-contrast color
- **AND** the rule MUST set `background:` to a non-transparent value so text contrast is measurable

#### Scenario: page-purpose-grid collapses to single column in collect

- **WHEN** `.page-purpose-card` is rendered inside `.collect-layout` (320–420px column)
- **THEN** the `.collect-layout > .page-purpose-card .page-purpose-grid` rule MUST set `grid-template-columns: 1fr` so Reads / Produces stack vertically
- **AND** the rule MUST set `gap` to at most `6px` to match the briefing context

#### Scenario: dt / dd text color in page-purpose-card meets contrast

- **WHEN** any `<dt>` or `<dd>` is rendered inside `.page-purpose-grid`
- **THEN** the rule MUST set `color:` to a value whose alpha is at least `0.85` (effective contrast ratio ≥ 4.5:1 against the page-purpose-card background)
- **AND** the rule MUST NOT use `opacity:` as the only contrast mechanism (opacity is multiplied with the background gradient, making effective contrast unpredictable)

### Requirement: Collect Layout Inherits App Shell Right Safe-Area

The Collect Workspace MUST NOT render any content (panel border, drop shadow, or text) within the right safe-area reserved by `.app-shell`. On narrow viewports (`<= 1024px`), the collect-sidecar MUST respect a horizontal padding so its panel borders do not touch the viewport edge.

#### Scenario: collect-sidecar respects narrow-viewport horizontal padding

- **WHEN** the viewport width is `<= 1024px`
- **THEN** the `@media (max-width: 1024px)` block MUST set a `padding-right` (or be wrapped in a parent with padding-right) on `.collect-sidecar` and `.collect-panel` so no panel border touches the right viewport edge
- **AND** the rule MUST set the right padding to a value consistent with the app-shell's mobile value (≤ `20px`)

#### Scenario: collect-layout grid does not extend past safe-area

- **WHEN** `.collect-layout` is rendered on a desktop viewport
- **THEN** the rule MUST keep the right column's `minmax(0, 1fr)` from exceeding the parent `.app-shell` content width (i.e. `100% - 80px - 320–420px left column - 18px gap`)
- **AND** the rule MUST NOT set an explicit `width:` or `max-width:` that overrides the grid track math

### Requirement: Source Switch Buttons Meet Accessibility Contrast

The `.source-switch` button (used to switch between GitHub / Papers / WeChat in the Collect source picker) MUST meet WCAG 1.4.11 (Non-text Contrast) for the unselected state. The border color of an unselected `.source-switch` MUST have an effective alpha of at least 0.30 against the panel background so the button outline is visible.

#### Scenario: Unselected source-switch has a visible border

- **WHEN** a `.source-switch` button is rendered in its default (non-`.active`) state
- **THEN** the `.source-switch` rule MUST override the shared `.tabbar button, ...` border to a color whose alpha is ≥ `0.30`
- **AND** the rule MUST NOT change the background or text color of the unselected state (only the border)

#### Scenario: Selected source-switch retains high contrast

- **WHEN** a `.source-switch.active` button is rendered
- **THEN** the `.source-switch.active` rule MUST keep its existing `background: linear-gradient(135deg, var(--accent) 0%, #115e59 100%)` and `color: #f8fffd`
- **AND** the new border-color override MUST NOT apply to `.source-switch.active` (selected state keeps its current visual treatment)
