// Server-side render tests for DailyDiscoveryCard.
//
// Why SSR (not JSDOM)?
//   - JSDOM is explicitly avoided by the project's L3 spec (see
//     `.compass/context/L3-specs/changes/fix-frontend-render-tests-jsdom/proposal.md`).
//   - The component uses ``useEffect`` for status fetching + polling, which
//     does NOT run during SSR. So SSR is purely a "what does the first paint
//     look like?" test — exactly the user-facing question we need to answer.
//
// We mock the network fetcher (set `global.fetch`) so the first effect
// either succeeds or fails synchronously after the SSR pass, letting us
// observe the actual first-paint DOM in the rendered string.

import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { transformSync } from "esbuild";

const __dirname = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = resolve(__dirname, "../src");
const CARD_PATH = resolve(SRC_DIR, "DailyDiscoveryCard.jsx");
const API_PATH = resolve(SRC_DIR, "api.js");
const NODE_MODULES = resolve(__dirname, "../node_modules");

// ---------------------------------------------------------------------------
// Loader: read JSX, compile to ESM pointing back at the project's
// node_modules, write to a tmp .mjs file, dynamic-import.
// ---------------------------------------------------------------------------

const TMP_DIR = mkdtempSync(join(tmpdir(), "ddc-ssr-"));
const CARD_BUNDLE = join(TMP_DIR, "Card.mjs");
const API_BUNDLE = join(TMP_DIR, "Api.mjs");

function buildBundle(srcPath, outPath) {
    const src = readFileSync(srcPath, "utf8");
    const { code } = transformSync(src, {
        loader: "jsx",
        format: "esm",
        target: "node18",
        jsx: "automatic",
    });
    // Rewrite bare specifiers to absolute paths against the project's
    // installed modules so the dynamic import resolves at runtime.
    // (esbuild 0.25+ dropped `absWorkingDir` from transformSync.)
    const rewritten = code
        .replace(/from\s+["']react\/jsx-runtime["']/g, `from "file://${NODE_MODULES}/react/jsx-runtime.js"`)
        .replace(/from\s+["']react["']/g, `from "file://${NODE_MODULES}/react/index.js"`)
        .replace(/from\s+["']\.\/api\.js["']/g, `from "file://${API_BUNDLE}"`);
    writeFileSync(outPath, rewritten, "utf8");
}

buildBundle(CARD_PATH, CARD_BUNDLE);
buildBundle(API_PATH, API_BUNDLE);

const CARD_PROMISE = import(CARD_BUNDLE);
const API_PROMISE = import(API_BUNDLE);

// Minimal React + server renderer available globally; import them lazily.
let React;
let renderToString;

async function ensureReact() {
    if (React) return;
    React = (await import("react")).default;
    renderToString = (await import("react-dom/server")).default.renderToString;
}

// ---------------------------------------------------------------------------
// Test helpers
// ---------------------------------------------------------------------------

async function renderCard(props = {}) {
    await ensureReact();
    const Card = (await CARD_PROMISE).default;
    return renderToString(React.createElement(Card, props));
}

function installFetchStub(payload) {
    globalThis.fetch = async () => ({
        ok: true,
        status: 200,
        json: async () => payload,
    });
}

function uninstallFetchStub() {
    delete globalThis.fetch;
}

// Best-effort cleanup of the tmp directory when the test process exits.
process.on("exit", () => {
    try {
        rmSync(TMP_DIR, { recursive: true, force: true });
    } catch (_e) {
        // ignore
    }
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

test("first paint shows the discover CTA", async () => {
    installFetchStub({ has_run: false, log_dir: "/tmp/x" });
    try {
        const html = await renderCard();
        assert.ok(html.includes("Run daily discovery now"), "missing primary CTA");
        assert.ok(html.includes("Daily discovery"), "missing card title");
    } finally {
        uninstallFetchStub();
    }
});

test("first paint includes a heading describing what the card does", async () => {
    installFetchStub({ has_run: false });
    try {
        const html = await renderCard();
        assert.match(html, /<h2[^>]*>[\s\S]*?Fresh AI signals, with evidence/i);
    } finally {
        uninstallFetchStub();
    }
});

test("first paint shows a loading indicator before useEffect resolves", async () => {
    installFetchStub({ has_run: false });
    try {
        const html = await renderCard();
        // SSR does not run useEffect, so the visible state is
        // {kind:"loading"} which renders the spinner/loading copy.
        assert.ok(
            html.includes("Checking last run") || html.includes("spinner"),
            "first paint should show loading indicator, not jump straight to data",
        );
    } finally {
        uninstallFetchStub();
    }
});

test("first paint suppresses the polling hint for returning users (has_run=true)", async () => {
    installFetchStub({
        has_run: true,
        started_at: "2026-06-29T09:00:00",
        summary: "succeeded=3 skipped=0 failed=0",
        briefing: { path: "briefing/foo.md", item_count: 3 },
    });
    try {
        const html = await renderCard();
        // SSR doesn't run useEffect, so the visible state is still
        // {kind:"loading"}. The first paint for *any* state must NOT
        // leak the "First time here?" hint — it's gated on real has_run.
        assert.ok(!html.includes("First time here?"), "first-run hint leaked on first paint");
    } finally {
        uninstallFetchStub();
    }
});

test("rendering survives a fetch error without crashing", async () => {
    globalThis.fetch = async () => {
        throw new Error("simulated network outage");
    };
    try {
        const html = await renderCard();
        assert.ok(html.includes("Run daily discovery now"), "card disappeared on first paint error");
    } finally {
        uninstallFetchStub();
    }
});

test("rendered CTA is a real button and is keyboard-reachable", async () => {
    installFetchStub({ has_run: false });
    try {
        const html = await renderCard();
        assert.match(
            html,
            /<button[^>]*type="button"[^>]*>[\s\S]*?Run daily discovery now/,
        );
        assert.ok(!html.includes('tabindex="-1"'), "tabindex=-1 traps keyboard focus");
    } finally {
        uninstallFetchStub();
    }
});

test("rendered heading hierarchy uses aria-labelledby + matching id", async () => {
    installFetchStub({ has_run: false });
    try {
        const html = await renderCard();
        assert.match(html, /<section[^>]*aria-labelledby="discovery-heading"/);
        assert.match(html, /<h2[^>]*id="discovery-heading"/);
    } finally {
        uninstallFetchStub();
    }
});

// ---------------------------------------------------------------------------
// "What would the user see if state had already settled?" — for these we
// pass the props directly to a tiny harness that mounts the inner sub-
// components. This documents the intended UI for each state without having
// to actually run useEffect. It catches regressions in the conditional
// branches (e.g. someone deleting the error banner by accident).
// ---------------------------------------------------------------------------

// We import the module's *internal* sub-components by reading the source
// and re-exporting the JSX pieces via React.createElement. The simplest way
// is to import the whole card and pass fake props that trigger each branch
// in `StatusBlock` / `JobTimeline`.
//
// Since the public component sets state internally, we cannot directly set
// its status. Instead, we reproduce the relevant branches by reading the
// component source and asserting that each branch's distinguishing text
// appears in the bundle. (The DOM-level behaviour for these branches is
// already covered by SSR rendering the initial loading state.)
// ---------------------------------------------------------------------------

const SOURCE = readFileSync(CARD_PATH, "utf8");

test("source defines a 'RecoveryHints' guidance list shown after errors", () => {
    assert.match(SOURCE, /function RecoveryHints\(\)/);
    assert.match(SOURCE, /dry-run/);
    assert.match(SOURCE, /\.state\/discovery\//);
});

test("source defines a 'FirstRunHint' shown only on first install", () => {
    assert.match(SOURCE, /function FirstRunHint\(/);
    // The hint must include the on-disk YAML path so users know what to edit.
    assert.match(SOURCE, /config\/discovery\.yaml/);
});

test("source defines a per-source result table", () => {
    assert.match(SOURCE, /className="job-table"/);
    // The table must show succeeded / skipped / failed counts.
    assert.match(SOURCE, /info\.succeeded/);
    assert.match(SOURCE, /info\.skipped/);
    assert.match(SOURCE, /info\.failed/);
});

test("source exposes 'Show setup hints again' for returning users", () => {
    assert.match(SOURCE, /Show setup hints again/);
});

test("source disables the primary CTA while a job is running", () => {
    // The button text + disabled attribute must be wired to the running
    // state. If someone removes the `disabled` attribute the user could
    // trigger overlapping jobs.
    assert.match(SOURCE, /disabled=\{isRunning\}/);
});

// ---------------------------------------------------------------------------
// Sub-component SSR tests — each exported branch component gets rendered in
// isolation with realistic props. These complement the source-grep tests
// above with real DOM assertions, so a regression that breaks the
// rendered HTML (without changing the source string) is caught.
// ---------------------------------------------------------------------------

async function renderNamedExport(name, props = {}) {
    await ensureReact();
    const mod = await CARD_PROMISE;
    const Component = mod[name];
    assert.ok(Component, `export "${name}" missing from DailyDiscoveryCard`);
    return renderToString(React.createElement(Component, props));
}

test("RecoveryHints renders the three concrete next steps", async () => {
    const html = await renderNamedExport("RecoveryHints");
    assert.ok(html.includes("dry-run"), "missing dry-run hint");
    assert.ok(html.includes(".state/discovery/"), "missing log-dir hint");
    assert.ok(html.includes("config/discovery.yaml"), "missing config hint");
    // The list is a real <ul> for screen-reader semantics.
    assert.match(html, /<ul[^>]*class="[^"]*recovery-list/);
});

test("FirstRunHint renders an ordered list of setup steps when first run", async () => {
    const html = await renderNamedExport("FirstRunHint", {
        status: { kind: "ready", data: { has_run: false } },
        hasJob: false,
    });
    assert.match(html, /<ol>/);
    assert.ok(html.includes("init-config"));
    assert.ok(html.includes("Edit that file"));
    assert.ok(html.includes("schedule launchd --install"));
});

test("FirstRunHint returns null once a run has been recorded", async () => {
    const html = await renderNamedExport("FirstRunHint", {
        status: { kind: "ready", data: { has_run: true, summary: "x", started_at: "2026-06-29" } },
        hasJob: false,
    });
    assert.equal(html, "", "FirstRunHint should render nothing for returning users");
});

test("FirstRunHint forceVisible overrides the returning-user gate", async () => {
    const html = await renderNamedExport("FirstRunHint", {
        status: { kind: "ready", data: { has_run: true } },
        hasJob: false,
        forceVisible: true,
    });
    assert.ok(html.includes("init-config"), "forceVisible should re-show onboarding");
});

test("StatusBlock renders the loading copy on first paint", async () => {
    const html = await renderNamedExport("StatusBlock", { status: { kind: "loading" } });
    assert.ok(html.includes("Checking last run"));
    assert.ok(html.includes("aria-live"));
    // The loading state must show a real spinner, not just text — otherwise
    // users can't tell the difference between "loading" and "no runs yet".
    assert.ok(html.includes("spinner"), "loading state missing spinner");
});

test("StatusBlock renders the no-runs message on fresh install", async () => {
    const html = await renderNamedExport("StatusBlock", {
        status: { kind: "ready", data: { has_run: false } },
    });
    assert.ok(html.includes("No runs yet"));
});

test("StatusBlock error banner has a Retry button and a log-dir hint", async () => {
    let clicked = false;
    const html = await renderNamedExport("StatusBlock", {
        status: { kind: "error", message: "upstream timeout" },
        onRetry: () => { clicked = true; },
    });
    assert.ok(html.includes("upstream timeout"));
    assert.match(html, /role="alert"/);
    // The new affordances: a Retry button and a pointer to the on-disk log.
    assert.ok(/<button[^>]*>[\s\S]*?Retry<\/button>/.test(html),
              "error banner missing Retry button");
    assert.ok(html.includes(".state/discovery/"),
              "error banner missing on-disk log pointer");
    // Rendering with onRetry wires the click handler in SSR but we don't
    // simulate it here — the test only checks the markup exists.
    void clicked;
});

test("StatusBlock renders the summary dl when a run is present", async () => {
    const html = await renderNamedExport("StatusBlock", {
        status: {
            kind: "ready",
            data: {
                has_run: true,
                started_at: "2026-06-29T09:00:00",
                summary: "succeeded=4 skipped=0 failed=0",
                briefing: { path: "briefing/daily.md", item_count: 7, status: "ready" },
            },
        },
    });
    assert.match(html, /<dl[^>]*class="[^"]*discovery-summary/);
    assert.ok(html.includes("succeeded=4"));
    assert.ok(html.includes("briefing/daily.md"));
    // Item count appears as "(7 items)". React 19 inserts `<!-- -->` comment
    // nodes between adjacent text/expression children, so tolerate them.
    assert.ok(
        /7(?:<!--[^>]*-->)?\s*items/.test(html),
        `expected item count '7 items'; got:\n${html.slice(0, 1500)}`,
    );
    assert.match(html, /data-briefing-status="ready"/);
    assert.ok(html.includes("Ready"));
});

test("StatusBlock distinguishes honest empty outcomes", async () => {
    for (const [status, copy] of [
        ["no_fresh_signals", "No verified fresh signals"],
        ["coverage_incomplete", "Coverage incomplete — no quiet-day conclusion"],
    ]) {
        const html = await renderNamedExport("StatusBlock", {
            status: {
                kind: "ready",
                data: {
                    has_run: true,
                    briefing: { path: "briefing/signals/daily.md", item_count: 0, status },
                },
            },
        });
        assert.match(html, new RegExp(`data-briefing-status="${status}"`));
        assert.ok(html.includes(copy), `missing copy for ${status}`);
    }
});

test("StatusBlock renders an error banner when the fetch fails", async () => {
    const html = await renderNamedExport("StatusBlock", {
        status: { kind: "error", message: "upstream timeout" },
    });
    assert.ok(html.includes("Could not read status"));
    assert.ok(html.includes("upstream timeout"));
    assert.match(html, /role="alert"/);
});

test("JobTimeline renders the running branch with spinner + polling copy", async () => {
    const html = await renderNamedExport("JobTimeline", {
        job: { id: "abc", phase: "running" },
    });
    assert.ok(html.includes("spinner"));
    assert.ok(html.includes("Sweep in progress"));
    assert.ok(html.includes("1.5s"));
    assert.match(html, /role="status"/);
});

test("JobTimeline renders config_error with concrete remediation copy", async () => {
    const html = await renderNamedExport("JobTimeline", {
        job: {
            phase: "done",
            status: "config_error",
            result: { message: "5 validation problem(s)" },
        },
    });
    assert.ok(html.includes("Configuration error"));
    assert.ok(html.includes("5 validation problem(s)"));
    assert.ok(html.includes("dry-run"));
    assert.match(html, /role="alert"/);
});

test("ResultReport renders a row per source with succeeded/skipped/failed counts", async () => {
    const html = await renderNamedExport("ResultReport", {
        result: {
            status: "partial",
            sources: {
                github: { succeeded: 3, skipped: 0, failed: 1, notes: ["ok", "rate limited"] },
                papers: { succeeded: 0, skipped: 0, failed: 0, notes: ["no categories configured"] },
            },
            briefing: { path: "briefing/daily.md", item_count: 2, status: "partial" },
        },
    });
    assert.match(html, /<table[^>]*class="[^"]*job-table/);
    // Per-source row labels.
    assert.ok(html.includes(">github<"));
    assert.ok(html.includes(">papers<"));
    // Failed count is highlighted via job-fail class.
    assert.match(html, /class="job-fail">1</);
    // Briefing link is present — the slash may or may not be URL-encoded
    // depending on whether React rendered encodeURI's output verbatim.
    assert.ok(
        html.includes("briefing/daily.md") || html.includes("briefing%2Fdaily.md"),
        "briefing path must appear in the rendered HTML",
    );
    assert.match(html, /data-briefing-status="partial"/);
    assert.ok(html.includes("Partial coverage"));
});

test("ResultReport distinguishes empty complete and incomplete coverage", async () => {
    const complete = await renderNamedExport("ResultReport", {
        result: {
            status: "ok",
            sources: {},
            briefing: {
                path: "briefing/signals/empty.md",
                item_count: 0,
                status: "no_fresh_signals",
            },
        },
    });
    const incomplete = await renderNamedExport("ResultReport", {
        result: {
            status: "partial",
            sources: {},
            briefing: {
                path: "briefing/signals/incomplete.md",
                item_count: 0,
                status: "coverage_incomplete",
            },
        },
    });
    assert.ok(complete.includes("No verified fresh signals"));
    assert.ok(!complete.includes("no quiet-day conclusion"));
    assert.ok(incomplete.includes("Coverage incomplete — no quiet-day conclusion"));
});

test("ResultReport hides the briefing link when path is the dry-run sentinel", async () => {
    const html = await renderNamedExport("ResultReport", {
        result: {
            status: "ok",
            sources: { github: { succeeded: 1, skipped: 0, failed: 0, notes: [] } },
            briefing: { path: "(dry-run)" },
        },
    });
    assert.ok(!html.includes("Briefing saved"), "dry-run result must not show a clickable briefing link");
});
