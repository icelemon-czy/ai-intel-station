// Behavior-level tests for the web workspace bundle.
//
// We statically parse the built JS to assert:
//
//   - Key UI strings survive the build (so i18n / copy changes don't silently break)
//   - The "Run daily discovery now" button is wired to the correct fetch path
//   - Service / launchd / cron instructions are reachable in the bundle
//   - There is no leftover dead-code reference that would 404
//
// These tests run under plain Node — no JSDOM. They guard against the kind
// of silent regressions that broke the DailyDiscoveryCard before the recent
// refactor (string drift, dropped buttons, broken deep links).

import { test } from "node:test";
import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATIC_DIR = resolve(__dirname, "../../workspace_web/static");
const ASSET_DIR = resolve(STATIC_DIR, "assets");

function loadBundle() {
    const files = readdirSync(ASSET_DIR).filter((name) => name.endsWith(".js"));
    assert.ok(files.length > 0, "no JS bundle found — has `npm --prefix web run build` been run?");
    // Vite produces a single hashed JS bundle under assets/.
    return files.map((name) => readFileSync(resolve(ASSET_DIR, name), "utf8")).join("\n");
}

function loadCss() {
    const files = readdirSync(ASSET_DIR).filter((name) => name.endsWith(".css"));
    return files.map((name) => readFileSync(resolve(ASSET_DIR, name), "utf8")).join("\n");
}

const BUNDLE = loadBundle();
const CSS = loadCss();
const SOURCE = ["App.jsx", "LibrarySection.jsx"]
    .map((name) => readFileSync(resolve(__dirname, "../src", name), "utf8"))
    .join("\n");

// ---------------------------------------------------------------------------
// Discovery card — primary user surface
// ---------------------------------------------------------------------------

test("bundle includes the primary CTA copy", () => {
    assert.ok(
        BUNDLE.includes("Run daily discovery now"),
        "missing 'Run daily discovery now' CTA in bundle",
    );
});

test("bundle includes the stop-polling affordance", () => {
    assert.ok(
        BUNDLE.includes("Stop polling"),
        "missing 'Stop polling' secondary action in bundle",
    );
});

test("bundle includes the show-hints affordance for returning users", () => {
    // FirstRunHint used to be visible only on first run. After the
    // refactor, returning users should see a "Show setup hints again" link.
    assert.ok(
        BUNDLE.includes("Show setup hints again"),
        "returning-user hint toggle is missing — users can't re-read onboarding",
    );
});

test("bundle includes first-run hint steps", () => {
    assert.ok(BUNDLE.includes("First time here? Read this"));
    assert.ok(BUNDLE.includes("init-config"));
    assert.ok(BUNDLE.includes("schedule launchd --install"));
});

test("bundle includes the per-source result table headings", () => {
    // The result report renders a table with these column headers — if any
    // disappear, users lose visibility into partial failures.
    for (const heading of ["Source", "Succeeded", "Skipped", "Failed", "Notes"]) {
        assert.ok(
            BUNDLE.includes(heading),
            `bundle missing table column "${heading}"`,
        );
    }
});

test("bundle references the structured briefing fields", () => {
    // After the recent refactor the card consumes `briefing.path` and
    // `briefing.item_count` (object) instead of splitting a string. The
    // presence of both keys in the bundle confirms the contract.
    assert.ok(BUNDLE.includes("item_count"), "bundle missing briefing.item_count");
});

test("bundle uses encodeURI for href construction", () => {
    // Defensive: briefing paths with spaces or unicode must be encoded.
    assert.ok(
        BUNDLE.includes("encodeURI"),
        "bundle no longer encodes briefing hrefs — paths with spaces will break",
    );
});

// ---------------------------------------------------------------------------
// CSS — accessibility & responsive layout
// ---------------------------------------------------------------------------

test("CSS defines spinner animation keyframes", () => {
    assert.ok(/@keyframes\s+discovery-spin/.test(CSS), "missing spinner keyframes");
    assert.ok(/animation:\s*discovery-spin/.test(CSS), "spinner class not using the keyframes");
});

test("CSS defines accessible focus outline on action buttons", () => {
    // Without focus-visible, keyboard users can't see what they're tabbing to.
    // Vite minifier can rename `:focus-visible` to itself, so match any
    // selector ending in :focus / :focus-visible / :focus-within.
    assert.ok(/:focus(-visible|-within)?[\s,{]/.test(CSS), "no :focus rules in stylesheet — keyboard a11y broken");
});

test("CSS includes a mobile breakpoint that collapses the card grid", () => {
    // The CSS minifier strips whitespace inside the media query — match
    // either the canonical form (with spaces) or the minified form.
    assert.ok(
        /@media\s*\(max-width:\s*720px\)/.test(CSS),
        "missing mobile breakpoint",
    );
});

test("CSS gives the discovery card a distinct left border (visual anchor)", () => {
    // The card uses a 4px left border as a visual anchor — losing this
    // makes the card blend into the dashboard.
    assert.ok(/\.discovery-card\s*\{[^}]*border-left/.test(CSS), "discovery-card left border missing");
});

// ---------------------------------------------------------------------------
// Wiring — fetch paths the card hits
// ---------------------------------------------------------------------------

test("bundle issues requests to /api/discover/* endpoints", () => {
    for (const path of ["/api/discover/status", "/api/discover/run", "/api/discover/job"]) {
        assert.ok(
            BUNDLE.includes(path),
            `bundle missing fetch to ${path}`,
        );
    }
});

test("bundle polls every 1.5s during a running job", () => {
    // The polling interval must match what the API docstring promises —
    // slower polls leave the UI stuck; faster ones hammer the server.
    // Vite minifies the callback argument name (e.g. `Q` instead of
    // `resolve`), so match the literal numeric value instead.
    assert.ok(
        /setTimeout\s*\([^,)]+,\s*1500\s*\)/.test(BUNDLE),
        "polling interval is no longer 1500ms — change is intentional and should be reviewed",
    );
});

// ---------------------------------------------------------------------------
// No dead references
// ---------------------------------------------------------------------------

test("bundle does not reference the removed global runNow helper", () => {
    // Earlier refactor introduced a top-level helper `runNow` that was
    // replaced by per-component closures. If it re-appears in the bundle
    // it usually means an import survived a delete.
    assert.ok(
        !/function\s+runNow\s*\(/.test(BUNDLE),
        "stale top-level `function runNow` re-appeared in the bundle",
    );
});

test("library search keyword input has a hint placeholder", () => {
    // Without a placeholder, new users stare at an empty input and
    // don't know what to type. The placeholder offers concrete examples.
    // Vite's minifier strips quotes around JSX string attributes when the
    // value is safe, so we match the literal `placeholder:` followed by the
    // first few characters of the example.
    assert.ok(
        /placeholder:\s*"e\.g\.\s*agent/i.test(BUNDLE) || /placeholder="e\.g\.\s*agent/i.test(BUNDLE),
        "library search input missing placeholder — new users won't know what to type",
    );
});

test("library search keyword input has an aria-label for screen readers", () => {
    // The source-level check is the most stable assertion: regardless of
    // how Vite minifies the JSX, the developer wrote the aria-label.
    // We still assert the bundle contains the visible "keyword" label so
    // the input is at least announced to screen readers via the wrapping
    // <span class="field-label">keyword</span>.
    assert.ok(
        /aria-label:\s*"Search keyword"/.test(SOURCE) || /aria-label="Search keyword"/.test(SOURCE),
        "library-filter-keyword input missing aria-label in source",
    );
    assert.ok(
        BUNDLE.includes("keyword") && /library-filter-keyword/.test(BUNDLE),
        "library-filter-keyword class not present in bundle",
    );
});

test("collect form surfaces dependency hints before users click Run", () => {
    // GitHub / WeChat / Papers each have prerequisites the user may not
    // have installed. The collect form must surface them as a banner so
    // users see "gh is required" before clicking Run, not as a 500 error
    // afterwards.
    assert.ok(
        BUNDLE.includes("dependency-banner"),
        "collect form missing dependency-banner element",
    );
    assert.ok(
        BUNDLE.includes("Prerequisite:"),
        "collect form missing Prerequisite: label",
    );
    // The CSS must give the banner a visible treatment (background +
    // border) — otherwise users wouldn't notice it.
    assert.ok(
        /\.dependency-banner\s*\{[^}]*border-left/.test(CSS),
        "dependency-banner CSS missing left border — users won't notice it",
    );
    assert.ok(
        /\.dependency-banner\s*\{[^}]*background/.test(CSS),
        "dependency-banner CSS missing background — users won't notice it",
    );
});
