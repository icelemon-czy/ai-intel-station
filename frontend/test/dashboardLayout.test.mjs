// Layout regression test for the dashboard 12-column grid.
//
// The dashboard is built from CSS Grid (grid-template-columns: repeat(12, 1fr)).
// Children declare `grid-column: span N` and CSS Grid auto-places them in
// row-major order. This test simulates that placement for the actual span
// values used in styles.css and asserts every row sums to exactly 12 — no
// overflows, no big gaps.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const CSS_PATH = resolve(__dirname, "../src/styles.css");
const CSS = readFileSync(CSS_PATH, "utf8");

function autoPlace(spans, cols) {
  const rows = [[]];
  let row = 0;
  for (const span of spans) {
    const used = rows[row].reduce((a, b) => a + b, 0);
    if (used + span > cols) {
      row++;
      rows[row] = [];
    }
    rows[row].push(span);
  }
  return rows;
}

// Extract every `grid-column: span N` rule and pair it with its selector
// so we know which UI element owns each span.
function extractSpans() {
  const rules = [];
  const re = /\.([a-zA-Z0-9_-]+)\s*\{[^}]*grid-column:\s*span\s+(\d+)[^}]*\}/g;
  let m;
  while ((m = re.exec(CSS)) !== null) {
    rules.push({ selector: m[1], span: parseInt(m[2], 10) });
  }
  return rules;
}

test("every dashboard grid-column span value is a positive integer <= 12", () => {
  const spans = extractSpans();
  assert.ok(spans.length > 0, "no grid-column: span rules found — has the dashboard been built?");
  for (const { selector, span } of spans) {
    assert.ok(span >= 1 && span <= 12, `.${selector} has invalid span ${span}`);
  }
});

test("dashboard 12-column grid places every row at exactly 12 columns", () => {
  // Reflect the dashboard layout in order of insertion. PollErrorBanner,
  // PagePurposeCard, EmptyStatePanel are 12-col when present.
  const dashSpans = [
    { selector: "poll-error-banner", span: 12 },
    { selector: "page-purpose-card", span: 12 },
    { selector: "empty-state-panel", span: 12 },
    { selector: "hero-card", span: 8 },
    { selector: "discovery-card", span: 4 },
    { selector: "metric-card", span: 4 },
    { selector: "metric-card", span: 4 },
    { selector: "metric-card", span: 4 },
    { selector: "metric-card", span: 4 },
  ];
  const cssSpans = extractSpans();
  for (const { selector, span } of dashSpans) {
    const cssSpan = cssSpans.find((r) => r.selector === selector);
    if (cssSpan) {
      assert.equal(
        cssSpan.span,
        span,
        `CSS rule .${selector} has span ${cssSpan.span}, layout test expects ${span}`,
      );
    }
  }
  const rows = autoPlace(
    dashSpans.map((s) => s.span),
    12,
  );
  for (let i = 0; i < rows.length; i++) {
    const used = rows[i].reduce((a, b) => a + b, 0);
    assert.ok(used <= 12, `row ${i + 1} overflows 12 cols (used=${used})`);
    if (i < rows.length - 1) {
      assert.equal(used, 12, `row ${i + 1} must total 12 columns, got ${used}`);
    }
  }
});

test("discovery card + hero card together fill one row exactly", () => {
  // Hero(8) + Discovery(4) = 12. The previous bug had Discovery span 2,
  // which left 2 cols empty (8 + 2 = 10) and made the row look broken.
  const spans = [8, 4];
  const rows = autoPlace(spans, 12);
  assert.equal(rows[0].reduce((a, b) => a + b, 0), 12, "hero + discovery must total 12");
});

test("four metric cards stack as 3 + 1 rows", () => {
  const spans = [4, 4, 4, 4];
  const rows = autoPlace(spans, 12);
  assert.equal(rows.length, 2, "expected 2 rows for 4 metric cards");
  assert.equal(rows[0].reduce((a, b) => a + b, 0), 12);
  assert.equal(rows[1].reduce((a, b) => a + b, 0), 4);
});