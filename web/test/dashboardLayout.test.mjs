// CSS schema regression test for the web workspace.
//
// This test does NOT render React or load JSDOM — it statically reads
// `web/src/styles.css` and asserts the key CSS rules introduced by
// `fix-web-dashboard-and-briefing-css-layout` are still present.
//
// Why static (not rendered) checks?
// - The project explicitly avoids JSDOM / Vitest (see
//   `.ai/L3-specs/changes/fix-frontend-render-tests-jsdom/proposal.md`
//   "Alternatives Considered").
// - `useEffect` does not run during SSR, so even with JSDOM the
//   Dashboard / Briefing components render their "Loading…" state, not
//   the loaded DOM we want to assert against.
// - The 4 categories of bugs we are guarding against are all "someone
//   reverted a CSS rule" — perfect for a static schema test.
//
// If a future refactor moves the rules around, the test will fail with
// a clear message naming the missing rule. That is the regression
// signal we want.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STYLES_PATH = resolve(__dirname, "../src/styles.css");
const CSS = readFileSync(STYLES_PATH, "utf8");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Extract the body of the Nth rule whose selector starts with `selector`.
 *
 * `selector` is a substring; the Nth `{ ... }` block after it is
 * returned (without the surrounding braces).  If no block is found,
 * returns `null` so the caller can produce a helpful error.
 *
 * `occurrence` is 0-indexed and defaults to 0 (first match).  This is
 * needed because the same selector substring can match multiple rules
 * (e.g. the global `button, input, select { font: inherit; }` shares
 * the `input, select` prefix with the actual styling rule further
 * down).
 */
function findRuleBody(selector, occurrence = 0) {
  let searchFrom = 0;
  let idx = -1;
  for (let i = 0; i <= occurrence; i++) {
    idx = CSS.indexOf(selector, searchFrom);
    if (idx === -1) return null;
    searchFrom = idx + selector.length;
  }
  const open = CSS.indexOf("{", idx);
  if (open === -1) return null;
  let depth = 1;
  let close = open + 1;
  while (close < CSS.length && depth > 0) {
    if (CSS[close] === "{") depth++;
    else if (CSS[close] === "}") depth--;
    close++;
  }
  return CSS.slice(open + 1, close - 1);
}

/**
 * Like findRuleBody but only returns the first body whose text contains
 * `mustContain`.  Used to skip the global `button, input, select {
 * font: inherit; }` rule and land on the real styling rule that has
 * `border-radius:` or `padding:` etc.
 *
 * `selector` can be a string (substring) or a RegExp.  When a regex is
 * passed, whitespace within the selector is normalized — useful for
 * matching `input, select {` (single space) and `input,\nselect {`
 * (newline) with the same search.
 */
function findRuleBodyContaining(selector, mustContain) {
  const re = selector instanceof RegExp
    ? new RegExp(selector.source, selector.flags.includes("g") ? selector.flags : selector.flags + "g")
    : null;
  let searchFrom = 0;
  while (true) {
    const idx = re ? (re.lastIndex = searchFrom, re.exec(CSS)?.index ?? -1) : CSS.indexOf(selector, searchFrom);
    if (idx === -1) return null;
    const open = CSS.indexOf("{", idx);
    if (open === -1) return null;
    let depth = 1;
    let close = open + 1;
    while (close < CSS.length && depth > 0) {
      if (CSS[close] === "{") depth++;
      else if (CSS[close] === "}") depth--;
      close++;
    }
    const body = CSS.slice(open + 1, close - 1);
    if (body.includes(mustContain)) return body;
    searchFrom = close;
  }
}

/**
 * Resolve the right padding from a CSS `padding:` shorthand body.
 *
 * CSS padding shorthand rules:
 *   1 value  → all four sides
 *   2 values → top/bottom, right/left
 *   3 values → top, right/left, bottom
 *   4 values → top, right, bottom, left
 *
 * We only care whether the resolved right padding matches the spec
 * (≥60px desktop, ≤20px mobile), not the literal shorthand form.
 */
function resolveRightPadding(body) {
  const match = body.match(/padding\s*:\s*([^;]+);/);
  if (!match) return null;
  const parts = match[1].trim().split(/\s+/);
  if (parts.length < 1 || parts.length > 4) return null;
  return parts.length === 1 ? parts[0] : parts[1];
}

/**
 * Check that a rule body contains an exact `property: value;` declaration
 * (ignoring surrounding whitespace).  This is stricter than a substring
 * search so a value like `border-radius: 100px` does not accidentally
 * match a check for `border-radius: 10px`.
 */
function ruleDeclares(body, property, value) {
  const re = new RegExp(`(^|;|\\n)\\s*${property}\\s*:\\s*${value}\\s*;`);
  return re.test(body);
}

// ---------------------------------------------------------------------------
// Requirement 1: Dashboard grid layout prevents card overlap
//   Spec: `.ai/L3-specs/changes/fix-web-dashboard-and-briefing-css-layout/
//         specs/research-web-workspace/spec.md` → "Dashboard Grid Layout
//         Prevents Card Overlap"
// ---------------------------------------------------------------------------

test("dashboard-grid top-stack rules make PagePurposeCard full-width", () => {
  // The selector is a comma-separated list.  The first branch is
  // `.dashboard-grid > .poll-error-banner` which is enough to locate the
  // shared rule body.
  const body = findRuleBody(".dashboard-grid > .poll-error-banner");
  assert.ok(body, "expected a rule for `.dashboard-grid > .poll-error-banner` (shared with .page-purpose-card and .empty-state-panel)");
  assert.ok(
    ruleDeclares(body, "grid-column", "1 / -1"),
    "expected `grid-column: 1 / -1` so PagePurposeCard, error banner, and empty-state panel each span the full 12-column track",
  );
  assert.ok(
    ruleDeclares(body, "align-self", "start"),
    "expected `align-self: start` so the full-width row does not stretch vertically",
  );
});

test("hero-card spans 8/12 columns and shrinks to its content", () => {
  const body = findRuleBody(".hero-card {");
  assert.ok(body, "expected a `.hero-card { ... }` rule");
  assert.ok(
    ruleDeclares(body, "grid-column", "span 8"),
    "expected `.hero-card` to span 8 of 12 columns (was `span 7` before the fix and caused the overlap bug)",
  );
  assert.ok(
    ruleDeclares(body, "min-height", "0"),
    "expected `min-height: 0` so the hero card shrinks to its content (the old `min-height: 180px` caused overflow at narrow widths)",
  );
});

test("metric-card renders as a real card and uses span 4", () => {
  const body = findRuleBody(".metric-card {");
  assert.ok(body, "expected a `.metric-card { ... }` rule");
  assert.ok(
    ruleDeclares(body, "grid-column", "span 4"),
    "expected `.metric-card` to span 4 of 12 columns (3-up row math: 4+4+4=12)",
  );
  // Card visual properties — the original CSS only set `grid-column`,
  // which is why the metric cards looked like invisible divs.
  assert.ok(
    /background\s*:/i.test(body),
    "expected `.metric-card` to declare `background:` — without it, the card is a transparent grid item and the hero card visually dominates",
  );
  assert.ok(
    ruleDeclares(body, "box-shadow", "var\\(--shadow\\)"),
    "expected `.metric-card` to use `box-shadow: var(--shadow)` for visual depth",
  );
  assert.ok(
    ruleDeclares(body, "border-radius", "24px"),
    "expected `.metric-card` to use `border-radius: 24px` consistent with the panel family",
  );
  assert.ok(
    ruleDeclares(body, "min-width", "0"),
    "expected `min-width: 0` to prevent text overflow at narrow column widths",
  );
});

test("metric-card.wide matches the 3-up row span", () => {
  const body = findRuleBody(".metric-card.wide");
  assert.ok(body, "expected a `.metric-card.wide` rule");
  assert.ok(
    ruleDeclares(body, "grid-column", "span 4"),
    "expected `.metric-card.wide` to use `span 4` (the old `span 6` would break the 3-up row math)",
  );
});

// ---------------------------------------------------------------------------
// Requirement 2: App shell reserves right safe-area
// ---------------------------------------------------------------------------

test("app-shell reserves right safe-area on desktop", () => {
  const body = findRuleBody(".app-shell {");
  assert.ok(body, "expected a `.app-shell { ... }` rule");
  // Accept any shorthand form (1/2/3/4 values) — what matters is the
  // RESOLVED right padding.  Threshold was raised from ≥60px to
  // ≥100px in `fix-web-dashboard-and-briefing-css-layout` (Bug 3):
  // the previous 60px satisfied a "future floating button" contract
  // but did not visually isolate the main content from the body
  // background's bottom-right orange gradient circle
  // (`radial-gradient(circle at bottom right, rgba(181, 84, 45, 0.14),
  // transparent 28%)` — visible up to ~28% of viewport width from the
  // right edge).  100px guarantees the content's right edge lands
  // well past the gradient's fade-in zone on a typical 1320px app
  // shell centered in a 1920px viewport.
  const right = resolveRightPadding(body);
  assert.ok(right, "expected `.app-shell` to declare a `padding:` shorthand");
  const px = parseInt(right, 10);
  assert.ok(
    px >= 100,
    `expected right padding to be ≥100px on desktop (visual isolation from the bottom-right orange gradient), got "${right}"`,
  );
});

test("app-shell reduces right padding on narrow viewports", () => {
  // Bracket-match the FIRST `@media (max-width: 1024px) { ... }` block
  // so we can search inside it for the `.app-shell` re-declaration.
  // The naive `indexOf("}", ...)` we tried first was wrong: it stopped
  // at the FIRST `}` it found, which belongs to an inner rule, not the
  // @media closing brace.
  const mediaIdx = CSS.indexOf("@media (max-width: 1024px)");
  assert.ok(mediaIdx >= 0, "expected a `@media (max-width: 1024px)` block");
  const mediaOpen = CSS.indexOf("{", mediaIdx);
  assert.ok(mediaOpen > mediaIdx, "expected an opening `{` for the @media block");
  let depth = 1;
  let mediaClose = mediaOpen + 1;
  while (mediaClose < CSS.length && depth > 0) {
    if (CSS[mediaClose] === "{") depth++;
    else if (CSS[mediaClose] === "}") depth--;
    mediaClose++;
  }
  const mediaBlock = CSS.slice(mediaOpen, mediaClose);
  const mobileAppShell = mediaBlock.match(/\.app-shell\s*\{([^}]*)\}/);
  assert.ok(mobileAppShell, "expected `.app-shell` to be re-declared inside the @media block");
  const right = resolveRightPadding(mobileAppShell[1]);
  assert.ok(right, "expected mobile `.app-shell` to declare a `padding:` shorthand");
  const px = parseInt(right, 10);
  assert.ok(
    px <= 20,
    `expected right padding to drop to ≤20px on narrow viewports, got "${right}"`,
  );
});

// ---------------------------------------------------------------------------
// Requirement 3: Briefing workspace density and action reachability
// ---------------------------------------------------------------------------

test("input and select use a 10px border-radius", () => {
  // The substring `input, select` also matches the global font-inherit
  // rule (`button, input, select { font: inherit; }`).  Use a
  // whitespace-tolerant regex so we can match both `input, select {`
  // (single space) and `input,\nselect {` (newline).  The
  // `findRuleBodyContaining` helper then skips past the font-inherit
  // body and lands on the actual styling rule that declares
  // `border-radius:`.
  const body = findRuleBodyContaining(/input\s*,\s*select\s*\{/, "border-radius");
  assert.ok(body, "expected a `input, select { ... }` rule that declares `border-radius`");
  assert.ok(
    ruleDeclares(body, "border-radius", "10px"),
    "expected `border-radius: 10px` (the old 14px pill style clashed with the panel's 24–28px)",
  );
  assert.ok(
    ruleDeclares(body, "padding", "10px 12px"),
    "expected `padding: 10px 12px` for consistent internal breathing",
  );
});

test("select uses appearance:none with a custom chevron", () => {
  // Find the standalone `select { ... }` rule that contains
  // `appearance:` (skips the global `button, input, select` rule).
  const body = findRuleBodyContaining("select {", "appearance");
  assert.ok(body, "expected a standalone `select { ... }` rule that declares `appearance`");
  assert.ok(
    /appearance\s*:\s*none/.test(body),
    "expected `appearance: none` so the browser's native chevron is replaced",
  );
  assert.ok(
    /-webkit-appearance\s*:\s*none/.test(body),
    "expected `-webkit-appearance: none` for Safari / older WebKit",
  );
  assert.ok(
    /background-image\s*:/.test(body),
    "expected a custom chevron via `background-image` (two linear-gradients forming a downward triangle)",
  );
  assert.ok(
    ruleDeclares(body, "padding-right", "32px"),
    "expected `padding-right: 32px` so the option text does not overlap the custom chevron",
  );
});

test("briefing-layout control-panel uses a 10px row gap", () => {
  const body = findRuleBody(".briefing-layout .control-panel {");
  assert.ok(body, "expected a `.briefing-layout .control-panel { ... }` rule");
  assert.ok(
    ruleDeclares(body, "gap", "10px"),
    "expected `gap: 10px` for compact form density (was 14px which pushed actions below the fold)",
  );
});

test("briefing-layout control-panel reserves bottom safe-area for sticky action row", () => {
  // The sticky action bar floats 16px above the viewport bottom and is
  // ~74px tall (14px padding + ~46px button + 14px padding).  When the
  // form content height exceeds the viewport, the last form fields
  // (Title, SOURCES) would scroll under the sticky bar unless the
  // control-panel reserves a `padding-bottom` safe-area.
  //
  // The form panel already has `padding: 22px` from `.panel`; the
  // briefing-specific override MUST set `padding-bottom` to at least
  // `100px` (90px for the bar + 10px breathing room) so the last
  // field can scroll fully above the bar.
  const body = findRuleBody(".briefing-layout .control-panel {");
  assert.ok(body, "expected a `.briefing-layout .control-panel { ... }` rule");
  const paddingMatch = body.match(/padding-bottom\s*:\s*([^;]+);/);
  assert.ok(
    paddingMatch,
    "expected `.briefing-layout .control-panel` to declare `padding-bottom` so the sticky action bar never hides the form's last fields",
  );
  const px = parseInt(paddingMatch[1].trim(), 10);
  assert.ok(
    px >= 100,
    `expected padding-bottom ≥ 100px (sticky-bar safe-area), got "${paddingMatch[1].trim()}"`,
  );
});

test("briefing-layout page-purpose-card drops the 18px margin-bottom", () => {
  // The selector may be `.briefing-layout > .page-purpose-card {` or a
  // comma-separated form `.briefing-layout > .page-purpose-card,
  // .collect-layout > .page-purpose-card {`.  We use
  // `findRuleBodyContaining` (the only helper in this file that
  // accepts a substring + mustContain filter) to land on the rule
  // body that actually declares `margin-bottom: 0`.
  const body = findRuleBodyContaining(".briefing-layout", "margin-bottom: 0");
  assert.ok(body, "expected a rule starting with `.briefing-layout` that contains `margin-bottom: 0`");
  assert.ok(
    ruleDeclares(body, "margin-bottom", "0"),
    "expected `margin-bottom: 0` so the parent grid gap is the only spacing (the old 18px stacked on the 18px grid gap)",
  );
  // Sub-grid: the `Reads / Produces` row in `.page-purpose-grid` should
  // collapse to single column in the narrow briefing column.  The
  // selector may be a comma-separated form too.
  const subBody = findRuleBodyContaining(
    ".briefing-layout > .page-purpose-card .page-purpose-grid",
    "grid-template-columns: 1fr",
  );
  assert.ok(subBody, "expected a sub-grid rule for `.page-purpose-grid` inside the briefing page-purpose card (optionally comma-separated with collect)");
  assert.ok(
    ruleDeclares(subBody, "grid-template-columns", "1fr"),
    "expected `grid-template-columns: 1fr` so Reads / Produces stack vertically in the 320–360px column",
  );
});

test("briefing action-row is a sticky bottom bar with frosted-glass background", () => {
  const body = findRuleBody(".briefing-layout .action-row {");
  assert.ok(body, "expected a `.briefing-layout .action-row { ... }` rule");
  assert.ok(
    ruleDeclares(body, "position", "sticky"),
    "expected `position: sticky` so the Preview / Save bar floats above scrolling content",
  );
  assert.ok(
    /bottom\s*:\s*16px/.test(body),
    "expected `bottom: 16px` so the bar sits 16px above the viewport bottom",
  );
  assert.ok(
    /z-index\s*:\s*5/.test(body),
    "expected `z-index: 5` so the sticky bar floats over content",
  );
  assert.ok(
    /background\s*:/.test(body),
    "expected a non-transparent `background:` so the bar is readable over scrolling content (the frosted-glass look)",
  );
  assert.ok(
    /backdrop-filter\s*:/.test(body),
    "expected `backdrop-filter:` for the frosted-glass effect",
  );
  // The 2-col grid must be overridden to flex so the buttons sit
  // side-by-side inside the floating pill.
  assert.ok(
    ruleDeclares(body, "display", "flex"),
    "expected `display: flex` to convert the action row from 2-col grid to a horizontal pill",
  );
  assert.ok(
    ruleDeclares(body, "grid-template-columns", "none"),
    "expected `grid-template-columns: none` to override the 2-col grid inherited from `.action-row`",
  );
});
