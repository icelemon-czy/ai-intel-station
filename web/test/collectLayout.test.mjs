// CSS schema regression test for the Collect Workspace.
//
// This test does NOT render React or load JSDOM — it statically reads
// `web/src/styles.css` and asserts the key CSS rules introduced by
// `fix-web-collect-workspace-layout` are still present.  See
// `web/test/dashboardLayout.test.mjs` for the rationale (the project
// avoids JSDOM, and `useEffect` does not run during SSR).
//
// If a future refactor reverts any of these rules, the test will fail
// with a clear message naming the missing property.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STYLES_PATH = resolve(__dirname, "../src/styles.css");
const CSS = readFileSync(STYLES_PATH, "utf8");

// ---------------------------------------------------------------------------
// Helpers (duplicated from dashboardLayout.test.mjs to keep this file
// standalone — the two test files cover different sections and should be
// runnable in isolation.)
// ---------------------------------------------------------------------------

/**
 * Find the body of the Nth rule whose selector matches `selectorRegex`,
 * returning the text between the matching `{` and its closing `}`.
 * Returns `null` if no match.
 */
function findRuleBody(selectorRegex, occurrence = 0) {
  const re = new RegExp(selectorRegex.source, selectorRegex.flags.includes("g") ? selectorRegex.flags : selectorRegex.flags + "g");
  let match;
  let count = 0;
  while ((match = re.exec(CSS)) !== null) {
    if (count === occurrence) {
      const open = CSS.indexOf("{", match.index);
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
    count++;
  }
  return null;
}

/**
 * Check that a rule body contains an exact `property: value;` declaration
 * (ignoring surrounding whitespace).
 */
function ruleDeclares(body, property, value) {
  const re = new RegExp(`(^|;|\\n)\\s*${property}\\s*:\\s*${value}\\s*;`);
  return re.test(body);
}

/**
 * Strip CSS block comments (`/* ... *​/`) from a rule body so the
 * caller can scan the actual declarations without false matches on
 * `opacity: 0.7` mentioned in a comment explaining why we removed it.
 */
function stripComments(body) {
  return body.replace(/\/\*[\s\S]*?\*\//g, "");
}

// ---------------------------------------------------------------------------
// Requirement 1: Collect Form Stays Above The Fold
//   Contract: `doc/web_workspace_design.md` → Collect workspace layout.
// ---------------------------------------------------------------------------

test("collect-layout empty-state-panel uses compact padding", () => {
  const body = findRuleBody(/\.collect-layout\s+\.empty-state-panel\s*\{/);
  assert.ok(body, "expected a `.collect-layout .empty-state-panel` rule");
  // Padding must be ≤ 12px on each side (compact mode inside collect)
  const paddingMatch = body.match(/padding\s*:\s*([^;]+);/);
  assert.ok(paddingMatch, "expected the collect empty-state-panel to declare `padding`");
  // Accept 1/2/3/4-value shorthand; the largest of the resolved values
  // is what we care about (the worst-case side).
  const parts = paddingMatch[1].trim().split(/\s+/);
  const pxValues = parts.map((p) => parseInt(p, 10));
  assert.ok(
    Math.max(...pxValues) <= 12,
    `expected padding values to be ≤ 12px in collect context, got "${paddingMatch[1].trim()}"`,
  );
});

test("collect-layout empty-state-panel inner font-size is compact", () => {
  // The CSS targets inner list items and paragraphs in collect context.
  // We look for a rule that includes `font-size` and targets the empty
  // state panel descendants.
  const body = findRuleBody(/\.collect-layout\s+\.empty-state-panel[^{]*\{/);
  assert.ok(body, "expected a `.collect-layout .empty-state-panel ...` rule");
  // Either the body itself or a follow-up rule in the same block
  // (e.g. `.collect-layout .empty-state-panel li { font-size: 13px }`)
  // must declare a compact font-size.  We grep the whole CSS for a rule
  // that contains both selectors, since the compact rule may be split.
  const compactRuleMatch = CSS.match(/\.collect-layout\s+\.empty-state-panel\s+(li|p)\s*\{([^}]*)\}/);
  if (compactRuleMatch) {
    const fontMatch = compactRuleMatch[2].match(/font-size\s*:\s*(\d+)px/);
    if (fontMatch) {
      assert.ok(
        parseInt(fontMatch[1], 10) <= 13,
        `expected font-size ≤ 13px, got ${fontMatch[1]}px`,
      );
      return;
    }
  }
  // Fallback: a single `font-size: 13px` inside the empty-state-panel
  // rule is acceptable.
  assert.ok(
    /font-size\s*:\s*1[23]px/.test(body),
    "expected the collect empty-state-panel to declare a compact font-size (≤ 13px)",
  );
});

test("collect-layout empty-state-panel supports a details/summary hook", () => {
  // The CSS must provide a `details > summary` selector inside the
  // collect empty-state-panel context, so a future JSX change can wrap
  // the FIRST RUN guidance in a collapsible <details>.
  const body = findRuleBody(/\.collect-layout\s+\.empty-state-panel\s+details\s*>\s*summary\s*\{/);
  assert.ok(body, "expected a `.collect-layout .empty-state-panel details > summary` rule (JSX hook for collapsible FIRST RUN guidance)");
  assert.ok(
    /cursor\s*:\s*pointer/.test(body),
    "expected `cursor: pointer` so the summary reads as clickable",
  );
});

// ---------------------------------------------------------------------------
// Requirement 2: PagePurposeCard Displays Reads And Produces With Sufficient
// Contrast
// ---------------------------------------------------------------------------

test("page-purpose-card declares an explicit base color and background", () => {
  // Match the STANDALONE `.page-purpose-card {` rule.  There are also
  // helper variants for `.dashboard-grid >`, `.briefing-layout >`, and
  // `.collect-layout > .page-purpose-card` — those inherit from this
  // base rule so the high-contrast color/background contract lives
  // here.
  const body = findRuleBody(/^\.page-purpose-card\s*\{/m);
  assert.ok(body, "expected a standalone `.page-purpose-card` rule");
  assert.ok(
    /(^|\n|;)\s*color\s*:/.test(body),
    "expected standalone `.page-purpose-card` to declare `color:` so child dt/dd inherit a high-contrast value",
  );
  assert.ok(
    /background\s*:/.test(body),
    "expected standalone `.page-purpose-card` to declare `background:` (the rule already does, but we lock it down)",
  );
});

test("page-purpose-card dt has a high-contrast color (alpha ≥ 0.85) and no opacity-based dilution", () => {
  const body = stripComments(findRuleBody(/\.page-purpose-grid\s+dt\s*\{/));
  assert.ok(body, "expected a `.page-purpose-grid dt` rule");
  // The fix must produce a rule whose EFFECTIVE text alpha is ≥ 0.85.
  // Two acceptable shapes:
  //   (a) `color: var(--ink)` (or any opaque value) with NO `opacity:`
  //       declared, or with `opacity: ≥ 0.85`
  //   (b) `color: rgba(..., <alpha>)` where the alpha is ≥ 0.85
  //
  // The pre-fix shape was `color: var(--ink); opacity: 0.7` — opaque
  // color, but `opacity: 0.7` diluted the effective alpha to 0.7, below
  // the 0.85 threshold.  The previous version of this test only
  // inspected the color value, so the bug slipped through as a false
  // pass.  The strengthened test now also asserts that `opacity:`
  // (when present) is ≥ 0.85.
  const colorMatch = body.match(/color\s*:\s*([^;]+);/);
  assert.ok(colorMatch, "expected `.page-purpose-grid dt` to declare `color:`");
  const colorValue = colorMatch[1].trim();
  if (colorValue.startsWith("rgba")) {
    const alphaMatch = colorValue.match(/,\s*([\d.]+)\s*\)/);
    assert.ok(
      alphaMatch && parseFloat(alphaMatch[1]) >= 0.85,
      `expected dt color rgba alpha ≥ 0.85, got "${colorValue}"`,
    );
  } else {
    // Non-rgba color (e.g. var(--ink), #152224) is opaque — alpha 1.0
    assert.ok(
      colorValue === "var(--ink)" || colorValue.startsWith("var(--ink)") || colorValue.startsWith("#"),
      `expected dt color to be var(--ink) / a hex code / an rgba with alpha ≥ 0.85, got "${colorValue}"`,
    );
  }
  // Effective alpha check: if the rule also declares `opacity:`, that
  // value multiplies with the color alpha, so it must itself be ≥ 0.85
  // to satisfy the 0.85 effective-alpha contract.  The pre-fix bug had
  // `opacity: 0.7` which the OLD version of this test missed.
  const opacityMatch = body.match(/opacity\s*:\s*([\d.]+)/);
  if (opacityMatch) {
    assert.ok(
      parseFloat(opacityMatch[1]) >= 0.85,
      `expected .page-purpose-grid dt opacity (when present) to be ≥ 0.85, got "${opacityMatch[1]}" — opacity multiplies with the background gradient, so 0.7 was making the 11px label nearly invisible`,
    );
  }
});

test("page-purpose-card dd declares an explicit color (not relying on inheritance)", () => {
  // The dd text inherits color from `.page-purpose-card` today
  // (`color: var(--ink)`), but that coupling is brittle: a future
  // style change to `.page-purpose-card` (e.g. a new gradient with a
  // darker color) could silently hide the dd text.  The spec requires
  // dd to declare its own `color:` so the visibility contract is
  // local to the rule.
  const body = findRuleBody(/\.page-purpose-grid\s+dd\s*\{/);
  assert.ok(body, "expected a `.page-purpose-grid dd` rule");
  assert.ok(
    /(^|\n|;)\s*color\s*:/.test(body),
    "expected `.page-purpose-grid dd` to declare an explicit `color:` (not rely on inheritance from `.page-purpose-card`)",
  );
});

test("page-purpose-card collapses to single column inside collect", () => {
  const body = findRuleBody(/\.collect-layout\s+>\s+\.page-purpose-card\s+\.page-purpose-grid\s*\{/);
  assert.ok(body, "expected a `.collect-layout > .page-purpose-card .page-purpose-grid` rule");
  assert.ok(
    ruleDeclares(body, "grid-template-columns", "1fr"),
    "expected `grid-template-columns: 1fr` so Reads / Produces stack vertically in the 320–420px collect column",
  );
});

// ---------------------------------------------------------------------------
// Requirement 3: Collect Layout Inherits App Shell Right Safe-Area
// ---------------------------------------------------------------------------

test("collect-sidecar respects narrow-viewport right padding", () => {
  // Find the @media (max-width: 1024px) block that contains a
  // `.collect-sidecar` rule.  There can be multiple such blocks
  // (e.g. one for `.app-shell` and one for the collect layout); we
  // want the one that targets collect specifically.
  const mediaBlockRe = /@media\s*\(max-width:\s*1024px\)\s*\{/g;
  let mediaMatch;
  let mediaBlock = null;
  while ((mediaMatch = mediaBlockRe.exec(CSS)) !== null) {
    const open = CSS.indexOf("{", mediaMatch.index);
    let depth = 1;
    let close = open + 1;
    while (close < CSS.length && depth > 0) {
      if (CSS[close] === "{") depth++;
      else if (CSS[close] === "}") depth--;
      close++;
    }
    const block = CSS.slice(open, close);
    if (/\.collect-(sidecar|panel|layout)/.test(block)) {
      mediaBlock = block;
      break;
    }
  }
  assert.ok(mediaBlock, "expected a `@media (max-width: 1024px)` block that contains a `.collect-*` rule");
  // Accept `.collect-sidecar` (optionally followed by `,` and another
  // selector) and the same for `.collect-panel`.  Also accept
  // `.collect-layout` for completeness.  We use `matchAll` to iterate
  // — the @media block may contain multiple `.collect-*` rules
  // (e.g. one for `grid-template-columns: 1fr` on the layout, another
  // for `padding-right: 0` on the sidecar/panel) and we want the one
  // that actually declares padding.
  const collectRuleRegex = /\.(collect-sidecar|collect-panel|collect-layout)(\s*,\s*\.(collect-sidecar|collect-panel|collect-layout))?\s*\{([^}]*)\}/g;
  const candidates = [...mediaBlock.matchAll(collectRuleRegex)];
  const padded = candidates.find((m) => /padding-right\s*:|padding\s*:\s*[^;]+/.test(m[m.length - 1]));
  assert.ok(
    candidates.length > 0,
    "expected at least one `.collect-*` rule inside the 1024px @media block",
  );
  assert.ok(
    padded,
    "expected a `.collect-*` narrow-viewport rule to declare padding (to keep the panel border off the viewport edge)",
  );
});

// ---------------------------------------------------------------------------
// Requirement 4: Source Switch Buttons Meet Accessibility Contrast
// ---------------------------------------------------------------------------

test("source-switch has a visible default border (alpha ≥ 0.30)", () => {
  // The shared rule `.tabbar button, .action-row button, .search-panel
  // button, .source-switch` uses `var(--line)` which is alpha 0.12 — too
  // faint.  We need a DEDICATED `.source-switch` rule (occurrence 1 in
  // CSS order, AFTER the shared comma-separated rule) that bumps the
  // border to alpha ≥ 0.30 for accessibility.
  const body = findRuleBody(/\.source-switch\s*\{/, 1);
  assert.ok(body, "expected a dedicated `.source-switch` rule (occurrence 1, after the shared comma-separated rule)");
  const borderMatch = body.match(/border(-color)?\s*:\s*([^;]+);/);
  assert.ok(borderMatch, "expected the dedicated `.source-switch` to declare a `border` or `border-color`");
  const borderValue = borderMatch[2].trim();
  if (borderValue.startsWith("rgba")) {
    const alphaMatch = borderValue.match(/,\s*([\d.]+)\s*\)/);
    if (alphaMatch) {
      assert.ok(
        parseFloat(alphaMatch[1]) >= 0.30,
        `expected source-switch border alpha ≥ 0.30 for WCAG 1.4.11, got "${borderValue}"`,
      );
      return;
    }
  }
  // A solid `var(--ink)` or any other non-transparent value is also fine.
  assert.ok(
    !borderValue.includes("var(--line)"),
    `source-switch border is still using var(--line) which has alpha 0.12 — not visible enough on a light background`,
  );
});

test("source-switch.active retains the selected-state gradient", () => {
  const body = findRuleBody(/\.source-switch\.active\s*\{/);
  assert.ok(body, "expected a `.source-switch.active` rule");
  assert.ok(
    /background\s*:\s*linear-gradient/.test(body),
    "expected `.source-switch.active` to keep the accent gradient background",
  );
  assert.ok(
    /color\s*:\s*#f8fffd/.test(body),
    "expected `.source-switch.active` to keep the white text color",
  );
});

// ---------------------------------------------------------------------------
// User-reported regression: "两个 workspace 的 web page 不 user-friendly"
// (Library + Collect).  The Run-now button and the Pagination / page-size
// controls were previously pushed below the fold on a 1280x800 viewport.
// Defensive CSS assertions lock in the layout shape that keeps them visible.
// ---------------------------------------------------------------------------

test("collect-panel is bounded so very tall forms scroll inside the panel", () => {
  const body = findRuleBody(/\.collect-panel\s*\{/);
  assert.ok(body, "expected a `.collect-panel` rule");
  assert.ok(
    /max-height\s*:\s*calc\(100vh\s*-\s*280px\)/.test(body),
    "collect-panel must bound its height so Run-now stays reachable on a 1024x768 viewport",
  );
  assert.ok(
    /overflow-y\s*:\s*auto/.test(body),
    "collect-panel must scroll vertically inside the panel — not the whole page",
  );
});

test("collect-panel action-row is sticky to the bottom of the panel", () => {
  const body = findRuleBody(/\.collect-panel\s+\.action-row\s*\{/);
  assert.ok(body, "expected a `.collect-panel .action-row` rule");
  assert.ok(
    /position\s*:\s*sticky/.test(body),
    "action-row must be sticky so Run-now stays visible while the form scrolls",
  );
  assert.ok(
    /bottom\s*:\s*0\b/.test(body),
    "sticky bottom must be 0 so the action row pins to the panel's visible bottom",
  );
  assert.ok(
    /background\s*:/.test(body),
    "sticky action-row needs a background so scrolling fields do not bleed through",
  );
});

test("purpose-card is a collapsible details, not a static aside", () => {
  // The previous JSX had `<aside class="purpose-card">` which occupied 350+ px
  // on a 1024x768 desktop, pushing form input fields out of the first
  // viewport. Collapsing it to a single-line `<summary>` reclaims that space.
  // We assert the CSS contract (collapsible summaries) rather than JSX.
  const body = findRuleBody(/\.purpose-card\s*\{/);
  assert.ok(body, "expected a `.purpose-card` rule");
  assert.ok(
    /padding\s*:\s*0\b/.test(body),
    ".purpose-card should not have its own padding — summary + dl now manage spacing",
  );
  const summary = findRuleBody(/\.purpose-card\s*>\s*summary\s*\{/);
  assert.ok(summary, "expected a `.purpose-card > summary` rule (collapsible summary)");
  assert.ok(
    /cursor\s*:\s*pointer/.test(summary),
    "summary must look clickable",
  );
});

test("collect-first-run-hint provides a compact collapsible summary", () => {
  const body = findRuleBody(/\.collect-first-run-hint\s*\{/);
  assert.ok(body, "expected a `.collect-first-run-hint` rule");
  assert.ok(
    /border\s*:\s*1px\s+dashed/.test(body),
    "first-run hint should look like an off-the-critical-path collapsible",
  );
  const summary = findRuleBody(/\.collect-first-run-hint\s*>\s*summary\s*\{/);
  assert.ok(summary, "expected a `.collect-first-run-hint > summary` rule");
  assert.ok(
    /text-transform\s*:\s*uppercase/.test(summary),
    "summary should be visually subordinate (uppercase eyebrow text)",
  );
});

test("collect-layout > page-purpose-card does not stretch beyond intrinsic height", () => {
  // The left aside was previously stretching to 1300+ px to match the
  // right form's intrinsic height, leaving 1100 px of empty whitespace.
  // `align-self: start` makes it shrink to fit content.
  const body = findRuleBody(/\.collect-layout\s*>\s*\.page-purpose-card\s*\{/);
  assert.ok(body, "expected a `.collect-layout > .page-purpose-card` rule");
  assert.ok(
    /align-self\s*:\s*start/.test(body),
    "page-purpose-card must align-self: start to avoid stretching and leaving empty whitespace",
  );
});

test("dashboard-grid > page-purpose-card does not stretch to row height", () => {
  // Same fix for the Dashboard's left rail.
  const body = findRuleBody(/\.dashboard-grid\s*>\s*\.page-purpose-card\s*\{/);
  assert.ok(body, "expected a `.dashboard-grid > .page-purpose-card` rule");
  assert.ok(
    /align-self\s*:\s*start/.test(body),
    "dashboard page-purpose-card must align-self: start",
  );
});
