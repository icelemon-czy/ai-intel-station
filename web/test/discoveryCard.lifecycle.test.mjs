// Multi-state SSR test — we render the same card with different props
// to simulate what a user would see across the lifecycle:
//   1. First paint (status="loading")
//   2. After fetch resolves (status="ready", data has_run=true)
//   3. After user clicks Run (job.phase="running")
//   4. After job completes (job.phase="done", result present)
//   5. Network error during initial load (status="error")
//
// Each render uses a fresh React state by constructing new elements with
// different prop combinations — this is what the user sees as they go
// through the flow, captured in the bundle and asserted in DOM.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = resolve(__dirname, "../src");
const CARD_PATH = resolve(SRC_DIR, "DailyDiscoveryCard.jsx");
const NODE_MODULES = resolve(__dirname, "../node_modules");

// Same build helper as the basic SSR test.
const { mkdtempSync, writeFileSync, rmSync } = await import("node:fs");
const { tmpdir } = await import("node:os");
const { join } = await import("node:path");
const { transformSync } = await import("esbuild");
const TMP_DIR = mkdtempSync(join(tmpdir(), "ddc-lifecycle-"));
const CARD_BUNDLE = join(TMP_DIR, "Card.mjs");
const API_BUNDLE = join(TMP_DIR, "Api.mjs");
{
    const src = readFileSync(CARD_PATH, "utf8");
    const { code } = transformSync(src, {
        loader: "jsx",
        format: "esm",
        target: "node18",
        jsx: "automatic",
    });
    const rewritten = code
        .replace(/from\s+["']react\/jsx-runtime["']/g, `from "file://${NODE_MODULES}/react/jsx-runtime.js"`)
        .replace(/from\s+["']react["']/g, `from "file://${NODE_MODULES}/react/index.js"`)
        .replace(/from\s+["']\.\/api\.js["']/g, `from "file://${API_BUNDLE}"`);
    writeFileSync(CARD_BUNDLE, rewritten, "utf8");
}
writeFileSync(API_BUNDLE, "export const requestJson = () => {};", "utf8");
process.on("exit", () => {
    try {
        rmSync(TMP_DIR, { recursive: true, force: true });
    } catch (_e) {}
});

const React = (await import("react")).default;
const { renderToString } = (await import("react-dom/server")).default;
const mod = await import(CARD_BUNDLE);
const DailyDiscoveryCard = mod.default;

// React's useEffect does not run during SSR, so the card always renders
// its INITIAL state. To simulate "user has been here for a while", we
// pre-populate status / job with the post-effect values via a thin
// harness: render a clone of the card's inner components with the
// values the running app would have. This is how snapshot tests of
// observed UI work.
const { StatusBlock, JobTimeline, ResultReport } = mod;

test("first paint: user sees loading state with spinner", () => {
    const html = renderToString(React.createElement(DailyDiscoveryCard));
    assert.ok(html.includes("spinner"), "loading spinner missing on first paint");
    assert.ok(html.includes("Checking last run"));
});

test("returning user sees summary dl with briefing link", () => {
    const status = {
        kind: "ready",
        data: {
            has_run: true,
            started_at: "2026-06-29T09:00:00",
            summary: "succeeded=3 skipped=0 failed=0",
            briefing: { path: "briefing/daily.md", item_count: 7 },
        },
    };
    const html = renderToString(React.createElement(StatusBlock, { status }));
    assert.ok(html.includes("succeeded=3"));
    assert.ok(html.includes("briefing/daily.md"));
    // React 19 inserts `<!-- -->` comments between adjacent children; tolerate.
    assert.ok(/7(?:<!--[^>]*-->)?\s*items/.test(html));
});

test("after Run click: user sees running timeline + Stop polling", () => {
    const job = { id: "abc123", phase: "running" };
    const html = renderToString(React.createElement(JobTimeline, { job }));
    assert.ok(html.includes("spinner"));
    assert.ok(html.includes("Sweep in progress"));
    assert.ok(html.includes("1.5s"));
});

test("after job completes: user sees per-source table with all rows", () => {
    const result = {
        status: "partial",
        sources: {
            github: { succeeded: 3, skipped: 0, failed: 1, notes: ["rate limited"] },
            papers: { succeeded: 0, skipped: 0, failed: 0, notes: ["no categories"] },
            wechat: { succeeded: 0, skipped: 0, failed: 0, notes: ["disabled"] },
        },
        briefing: { path: "briefing/daily.md" },
    };
    const html = renderToString(React.createElement(ResultReport, { result }));
    // All three source rows present.
    for (const src of ["github", "papers", "wechat"]) {
        assert.ok(html.includes(`>${src}<`), `missing ${src} row`);
    }
    // Failed count highlighted.
    assert.match(html, /class="job-fail">1</);
    // Briefing link.
    assert.ok(html.includes("briefing/daily.md"));
});

test("network error during initial load: user sees error + Retry button", () => {
    const status = { kind: "error", message: "fetch failed: ECONNREFUSED" };
    const html = renderToString(React.createElement(StatusBlock, {
        status,
        onRetry: () => {},
    }));
    assert.match(html, /role="alert"/);
    assert.ok(html.includes("ECONNREFUSED"));
    assert.ok(/<button[^>]*>[\s\S]*?Retry<\/button>/.test(html),
              "missing Retry button");
    assert.ok(html.includes(".ai/L4-session/discovery/"));
});

test("non-error state never shows a Retry button", () => {
    const html = renderToString(React.createElement(StatusBlock, {
        status: { kind: "ready", data: { has_run: false } },
        onRetry: () => {},
    }));
    assert.ok(!html.includes("Retry</button>"),
              "Retry button must only appear in error state");
});

test("error state without onRetry callback omits Retry button", () => {
    const html = renderToString(React.createElement(StatusBlock, {
        status: { kind: "error", message: "boom" },
    }));
    assert.ok(!html.includes("Retry</button>"),
              "Retry button must require an onRetry prop");
});

test("disabled state on Run button is wired to job phase", () => {
    // Read source: the disabled attribute must reference isRunning (the
    // computed boolean), not e.g. a hard-coded true. This guards against
    // a regression where someone wires it to `loading` only.
    const src = readFileSync(CARD_PATH, "utf8");
    assert.match(src, /disabled=\{isRunning\}/);
});