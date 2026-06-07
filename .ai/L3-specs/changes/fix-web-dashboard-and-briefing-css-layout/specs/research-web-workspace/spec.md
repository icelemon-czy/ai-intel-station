# research-web-workspace — Delta Spec

> 本文件描述对 `specs/research-web-workspace/spec.md` 的增量变更。
> 归档时 Agent 会把这些新增的 Requirement 合并到主 spec 中。

## ADDED Requirements

### Requirement: Dashboard Grid Layout Prevents Card Overlap

The Dashboard section (`<section class="dashboard-grid">`) MUST lay out the page-purpose card, the error banner, and the empty-state panel as **full-width rows** that do not share a grid track with the hero card or any metric card. The hero card and metric cards MUST each be assigned an explicit `grid-column` span so they do not auto-place into the narrow column reserved for full-width children. Every dashboard grid item MUST have `align-self: start` and `min-height: 0` so cards do not stretch to a fixed 180px row height and do not overflow their column at narrow viewports.

#### Scenario: PagePurposeCard occupies its own full-width row

- **WHEN** the Dashboard renders the PagePurposeCard as a direct child of `.dashboard-grid`
- **THEN** the CSS rule `.dashboard-grid > .page-purpose-card` MUST set `grid-column: 1 / -1` so the card spans the full 12-column track on its own row
- **AND** the rule MUST set `align-self: start` so the card does not stretch vertically

#### Scenario: Hero card uses an explicit column span

- **WHEN** the Dashboard renders `.hero-card` as a direct child of `.dashboard-grid`
- **THEN** the CSS rule MUST set `grid-column: span 8` (8 of 12 tracks)
- **AND** the rule MUST set `min-height: 0` so the card shrinks to its content rather than enforcing a 180px row

#### Scenario: Metric cards use uniform spans that sum to 12 per row

- **WHEN** the Dashboard renders the four `.metric-card` elements (source coverage, coverage gaps, recent briefings, orphan markdown) as direct children of `.dashboard-grid`
- **THEN** each `.metric-card` rule MUST set `grid-column: span 4` so 3 cards fit per row (4 + 4 + 4 = 12)
- **AND** `.metric-card.wide` MUST use the same `span 4` (not `span 6`) so the 3-up row math holds

#### Scenario: Metric cards render as visible cards, not bare divs

- **WHEN** the Dashboard renders any `.metric-card` element
- **THEN** the CSS rule MUST declare `background:`, `border:`, `border-radius:`, `padding:`, and `box-shadow:` — the card MUST be visually distinct from the surrounding panel background, not a transparent grid item
- **AND** the card MUST have `min-width: 0` to prevent text overflow at narrow column widths

#### Scenario: Narrow viewport collapses dashboard to single column

- **WHEN** the viewport width is `<= 1024px`
- **THEN** the `@media (max-width: 1024px)` rule MUST collapse `.dashboard-grid` to `grid-template-columns: 1fr`
- **AND** the rule MUST set `.hero-card` and `.metric-card` to `grid-column: 1 / -1` so each card spans the full row

### Requirement: App Shell Reserves Right Safe-Area

The `.app-shell` root container MUST reserve at least 60px of right padding at desktop widths so that future floating action elements (e.g. a circular "new run" button) do not crowd or overlap the main content's right edge.

#### Scenario: Desktop right padding reserves safe area

- **WHEN** the viewport width is `> 1024px`
- **THEN** the `.app-shell` rule MUST set `padding-right` to at least `100px` so the main content (Dashboard / Library / Briefing / Collect) is visually isolated from both future fixed-position floating actions AND the body background's bottom-right orange gradient circle (`radial-gradient(circle at bottom right, rgba(181, 84, 45, 0.14), transparent 28%)` — visible up to ~28% of the viewport width from the right edge)
- **AND** the right safe-area MUST be at least 20px larger than the body's gradient-fade distance so the content's right edge always lands in the body's "neutral" (no gradient) zone, not on the gradient's fade-in zone

#### Scenario: Narrow viewport reduces right padding

- **WHEN** the viewport width is `<= 1024px`
- **THEN** an `@media (max-width: 1024px)` rule MUST reduce `.app-shell` `padding-right` back to `20px` so the content can use the full mobile width

### Requirement: Briefing Workspace Density And Action Reachability

The Briefing Workspace MUST use compact form spacing, consistent input styling, and a sticky action bar so users can reach the primary "Preview briefing" and "Save" actions without scrolling past the form, flow note, and supporting text.

#### Scenario: Form controls use a 10px border-radius consistent with the panel family

- **WHEN** any `<input>` or `<select>` is rendered in the web workspace
- **THEN** the `input, select` CSS rule MUST set `border-radius: 10px` (a midpoint between the 14px pill style and a sharp 4–6px edge)
- **AND** the rule MUST set `padding: 10px 12px` for consistent internal text breathing

#### Scenario: Select dropdown uses a custom chevron

- **WHEN** any `<select>` is rendered
- **THEN** the `select` CSS rule MUST set `appearance: none` and `-webkit-appearance: none`
- **AND** the rule MUST declare a `background-image` containing two linear-gradients positioned to render a downward chevron, plus `padding-right: 32px` to keep the chevron from overlapping the option text

#### Scenario: Control panel uses compact 10px row gap

- **WHEN** `.control-panel` is rendered inside `.briefing-layout`
- **THEN** the `.briefing-layout .control-panel` rule MUST set `gap: 10px` (not the default 14px) so the form fits in a 320–360px column without forcing the action bar below the fold
- **AND** labels and flow notes inside this panel MUST use a 6px internal gap

#### Scenario: PagePurposeCard in briefing uses single-column sub-grid

- **WHEN** `.page-purpose-card` is rendered as a direct child of `.briefing-layout`
- **THEN** the `.briefing-layout > .page-purpose-card` rule MUST set `margin-bottom: 0` (the parent grid gap already provides spacing)
- **AND** the rule MUST collapse the `.page-purpose-grid` to `grid-template-columns: 1fr` with `gap: 6px` so Reads / Produces stack vertically in the narrow 320–360px column

#### Scenario: PagePurposeCard dt and dd labels are fully visible against the green gradient

- **WHEN** `.page-purpose-card` is rendered inside `.briefing-layout` (or any section that uses the green gradient background)
- **THEN** the `.page-purpose-grid dt` rule MUST declare `color:` with a value whose effective alpha is at least `0.85` (NOT rely on `opacity:` — opacity multiplies with the background gradient, making the effective contrast unpredictable; on a light-green gradient, 11px 70%-alpha text becomes nearly invisible)
- **AND** the rule MUST NOT declare an `opacity:` property whose value is less than `0.85`
- **AND** the `.page-purpose-grid dd` rule MUST declare an explicit `color:` (not rely on inheritance from `.page-purpose-card`) so a future card-color change cannot accidentally hide the dd text

#### Scenario: Action row is a sticky bottom bar

- **WHEN** `.action-row` is rendered inside `.briefing-layout .control-panel`
- **THEN** the `.briefing-layout .action-row` rule MUST set `position: sticky; bottom: 16px`
- **AND** the rule MUST set `z-index: 5` (or higher) so the bar floats over scrolling content
- **AND** the rule MUST set a non-transparent `background:` (e.g. `rgba(255, 252, 245, 0.86)`) plus `backdrop-filter: blur(…)` so the bar is readable when content scrolls under it
- **AND** the rule MUST convert the row from a 2-column grid to a flex container (`grid-template-columns: none; display: flex`) so the buttons stack side-by-side inside the floating pill

#### Scenario: Sticky action bar degrades on narrow viewports

- **WHEN** the viewport width is `<= 1024px`
- **THEN** the `@media (max-width: 1024px)` rule MUST drop the negative margin that extends the bar to the panel edge
- **AND** the rule MUST add a 1px border and `border-radius: 18px` so the bar reads as a discrete button group, not a docked footer

#### Scenario: Form content remains reachable above sticky action bar

- **WHEN** the briefing form's vertical content height (Mode + Keyword + Title + SOURCES + supporting paragraphs) exceeds the viewport height so the sticky action bar would otherwise cover the last form fields
- **THEN** the `.briefing-layout .control-panel` rule MUST reserve a `padding-bottom` of at least `100px` so the form's last fields (Title input, SOURCES toggles) can scroll to a position fully above the sticky action bar
- **AND** the rule MUST keep this `padding-bottom` at all viewport widths (no media-query override) so the safe-area is always reserved when the form overflows
- **AND** the rule MUST NOT push the action row's sticky `bottom` offset above `16px` — the clearance comes from the form's `padding-bottom`, not from re-positioning the bar
