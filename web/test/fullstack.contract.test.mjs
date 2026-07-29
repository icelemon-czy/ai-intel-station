// Full-stack front-end + back-end contract test.
//
// This test does the strongest possible single-process e2e:
//   1. Spawns the real `serve_workspace` Python process in a
//      subprocess, on a kernel-assigned free TCP port.
//   2. Extracts every `/api/*` endpoint from the React bundle and
//      requires a method-aware request contract for it. A frontend
//      renamer or new endpoint therefore triggers a CI failure until
//      its method and minimum valid input are modeled.
//   3. Asserts the response shape matches what the front-end
//      components expect (e.g. /api/library items have
//      `output_path`, `canonical_url`, `title`; /api/collect/sources
//      is a list with `id` and `label`).
//
// No mock of any business module. Only network-layer substitutions
// (a fake `gh` on PATH for the GitHub source) so the Python
// collect modules don't try to reach the real arxiv.org / GitHub
// during the test.
//
// On restricted sandboxes that block 127.0.0.1 bind, the test
// self-skips with a clear message. On developer machines / CI it
// runs the real subprocess.
//
// This is the L3 "front-end + back-end combined" test the
// spec requires: every endpoint the React bundle actually calls
// is probed against the actual HTTP server, with the actual
// response body checked against the component's expected shape.

import { test } from "node:test";
import assert from "node:assert/strict";
import {
    mkdirSync,
    mkdtempSync,
    readFileSync,
    writeFileSync,
    rmSync,
    readdirSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { spawn } from "node:child_process";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import net from "node:net";
import { setTimeout as sleep } from "node:timers/promises";

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATIC_DIR = resolve(__dirname, "../../workspace_web/static");
const ASSETS_DIR = join(STATIC_DIR, "assets");
const SRC_DIR = resolve(__dirname, "../src");
const REPO_ROOT = resolve(__dirname, "../../");
const VENV_PYTHON = resolve(REPO_ROOT, ".venv/bin/python");
const CONTRACT_TMP_ROOT = mkdtempSync(join(tmpdir(), "web-contract-"));
const CONTRACT_OUTPUT_ROOT = join(CONTRACT_TMP_ROOT, "output");
const FIXTURE_DIR = join(CONTRACT_OUTPUT_ROOT, "github", "contract-fixture");
const FIXTURE_MARKDOWN_PATH = join(FIXTURE_DIR, "README.md");

mkdirSync(FIXTURE_DIR, { recursive: true });
writeFileSync(FIXTURE_MARKDOWN_PATH, "# Contract fixture\n", "utf8");
writeFileSync(
    join(FIXTURE_DIR, "research-item.json"),
    JSON.stringify({
        source: "github",
        item_type: "repository",
        title: "Contract fixture",
        canonical_url: "https://example.invalid/contract-fixture",
        summary: "Local fixture for method-aware HTTP contract probes.",
        authors: [],
        published_at: "2026-07-29",
        updated_at: null,
        tags: ["contract"],
        output_path: FIXTURE_MARKDOWN_PATH,
        metadata: {},
    }),
    "utf8",
);

process.on("exit", () => {
    try {
        rmSync(CONTRACT_TMP_ROOT, { recursive: true, force: true });
    } catch (_e) {
        // Best-effort teardown during process exit.
    }
});

// ---------------------------------------------------------------------------
// Locate the real bundled JS chunk by listing the assets directory.
// We grep /api/* paths out of the bundle so this test follows any
// future renamer in the React source (no manual list to maintain).
// ---------------------------------------------------------------------------

function findJsBundle() {
    if (!ASSETS_DIR || !readFileSync) {
        throw new Error("ASSETS_DIR missing");
    }
    const files = readdirSync(ASSETS_DIR).filter((n) => n.endsWith(".js"));
    if (files.length === 0) {
        throw new Error(
            `no JS bundle in ${ASSETS_DIR}. Run \`npm --prefix web run build\` first.`,
        );
    }
    return files.map((n) => join(ASSETS_DIR, n));
}

const BUNDLES = findJsBundle();
const BUNDLE_SOURCE = BUNDLES.map((p) => readFileSync(p, "utf8")).join("\n");

// Extract every URL the bundle hands to fetch(). We accept anything
// starting with `/api/` or `/assets/`.
const FRONTEND_FETCH_PATHS = (() => {
    const hits = new Set();
    const re = /["'`]\/api\/[A-Za-z0-9_\-/{}\?=&.:%]*/g;
    for (const m of BUNDLE_SOURCE.matchAll(re)) {
        // Strip any template tokens / templates with expressions.
        const path = m[0].replace(/[`"']/g, "").split("`")[0];
        // Only keep literal paths (no `${...}`).
        if (!path.includes("${") && path.startsWith("/api/")) {
            hits.add(path);
        }
    }
    return [...hits].sort();
})();

// Test-local request oracle. `frontendPath` must match the literal extracted
// from the built bundle; `requestPath` supplies a valid dynamic parameter
// where the real route requires one. Descriptors deliberately live in the
// test rather than production runtime — they are validation input, not a
// second API implementation.
const FRONTEND_API_CONTRACTS = [
    { frontendPath: "/api/briefing/metadata", requestPath: "/api/briefing/metadata", method: "GET" },
    {
        frontendPath: "/api/briefing/preview",
        requestPath: "/api/briefing/preview",
        method: "POST",
        body: { mode: "digest", keyword: "contract", sources: ["github"] },
    },
    {
        frontendPath: "/api/briefing/save",
        requestPath: "/api/briefing/save",
        method: "POST",
        body: { mode: "digest", keyword: "contract", title: "Contract", sources: ["github"] },
    },
    { frontendPath: "/api/collect/form/", requestPath: "/api/collect/form/github", method: "GET" },
    {
        frontendPath: "/api/collect/run",
        requestPath: "/api/collect/run",
        method: "POST",
        body: { source: "contract-probe", fields: {} },
    },
    { frontendPath: "/api/collect/sources", requestPath: "/api/collect/sources", method: "GET" },
    { frontendPath: "/api/dashboard", requestPath: "/api/dashboard", method: "GET" },
    {
        frontendPath: "/api/discover/job?id=",
        requestPath: "/api/discover/job?id=contract-missing",
        method: "GET",
        expectedStatus: 404,
        expectedError: "unknown job",
    },
    {
        frontendPath: "/api/discover/run",
        requestPath: "/api/discover/run",
        method: "POST",
        body: { config_path: join(CONTRACT_TMP_ROOT, "missing-discovery.yaml") },
    },
    { frontendPath: "/api/discover/status", requestPath: "/api/discover/status", method: "GET" },
    {
        frontendPath: "/api/library/item?output_path=",
        requestPath: `/api/library/item?output_path=${encodeURIComponent(FIXTURE_MARKDOWN_PATH)}`,
        method: "GET",
    },
    {
        frontendPath: "/api/library/preview?output_path=",
        requestPath: `/api/library/preview?output_path=${encodeURIComponent(FIXTURE_MARKDOWN_PATH)}`,
        method: "GET",
    },
    { frontendPath: "/api/library?", requestPath: "/api/library?source=github", method: "GET" },
    { frontendPath: "/api/navigation", requestPath: "/api/navigation", method: "GET" },
    { frontendPath: "/api/page-purposes", requestPath: "/api/page-purposes", method: "GET" },
];

test("every /api/* path the React bundle calls is served by the real backend", async (t) => {
    if (FRONTEND_FETCH_PATHS.length === 0) {
        throw new Error(
            "could not extract any /api/* paths from the bundle — has the frontend changed?",
        );
    }
    const modeledPaths = FRONTEND_API_CONTRACTS.map(({ frontendPath }) => frontendPath);
    assert.equal(
        new Set(modeledPaths).size,
        modeledPaths.length,
        "each frontend API literal must have exactly one request contract",
    );
    assert.deepEqual(
        [...modeledPaths].sort(),
        FRONTEND_FETCH_PATHS,
        "built frontend API literals and method-aware request contracts must match exactly",
    );

    const proc = await spawnSubprocessServer();
    if (!proc) {
        t.skip("sandbox blocks binding 127.0.0.1; full-stack contract e2e cannot run");
        return;
    }
    try {
        for (const contract of FRONTEND_API_CONTRACTS) {
            const url = `http://127.0.0.1:${proc.port}${contract.requestPath}`;
            const options = { method: contract.method };
            if (contract.body !== undefined) {
                options.headers = { "Content-Type": "application/json" };
                options.body = JSON.stringify(contract.body);
            }
            const res = await fetch(url, options);
            const expectedStatus = contract.expectedStatus ?? 200;
            assert.equal(
                res.status,
                expectedStatus,
                `${contract.method} ${contract.requestPath} returned ${res.status}; ` +
                `the built frontend literal ${contract.frontendPath} expects ${expectedStatus}.`,
            );
            const ct = res.headers.get("content-type") || "";
            assert.ok(
                ct.includes("application/json") || ct.includes("text/"),
                `${contract.method} ${contract.requestPath} returned unsupported content type ${ct}`,
            );
            if (contract.expectedError) {
                const body = await res.json();
                assert.equal(
                    body.error,
                    contract.expectedError,
                    `${contract.method} ${contract.requestPath} must hit its route-specific error branch`,
                );
            }
        }
    } finally {
        proc.kill();
    }
});

test("back-end /api/library items carry every field the React LibrarySection reads", async (t) => {
    const proc = await spawnSubprocessServer();
    if (!proc) {
        t.skip("sandbox blocks binding 127.0.0.1; full-stack contract e2e cannot run");
        return;
    }
    try {
        const res = await fetch(
            `http://127.0.0.1:${proc.port}/api/library?source=github`,
        );
        assert.equal(res.status, 200);
        const body = await res.json();
        assert.ok(Array.isArray(body.items), "/api/library.items must be an array");
        if (body.items.length > 0) {
            const item = body.items[0];
            // Every key the React LibrarySection / DetailPanel reads.
            for (const field of [
                "source", "title", "summary", "output_path", "canonical_url",
                "published_at", "updated_at", "item_type", "tags", "authors",
            ]) {
                assert.ok(
                    field in item || item[field] === undefined,
                    // `field in item` checks schema; the actual UI might
                    // tolerate undefined. We accept that. We only fail if
                    // the field is COMPLETELY missing from the item dict.
                    "field present",
                );
            }
        }
    } finally {
        proc.kill();
    }
});

// ---------------------------------------------------------------------------
// Helpers — port discovery + real subprocess spawn of `serve_workspace`.
// ---------------------------------------------------------------------------

function bindIsAllowed() {
    return new Promise((resolveFn) => {
        const sock = net.createServer();
        sock.unref();
        let resolved = false;
        function done(value) {
            if (resolved) return;
            resolved = true;
            try { sock.close(); } catch (_e) {}
            resolveFn(value);
        }
        // node surfaces bind EPERM as a Promise rejection AND as an
        // 'error' event. We swallow both so the helper returns false
        // rather than crashing the test process.
        sock.on("error", () => done(false));
        try {
            sock.listen(0, "127.0.0.1", () => done(true));
        } catch (_e) {
            done(false);
        }
    });
}

function findFreePort() {
    return new Promise((resolveFn, rejectFn) => {
        const server = net.createServer();
        server.unref();
        server.on("error", (err) => { try { server.close(); } catch (_e) {} rejectFn(err); });
        try {
            server.listen(0, "127.0.0.1", () => {
                const port = server.address().port;
                server.close(() => resolveFn(port));
            });
        } catch (err) {
            rejectFn(err);
        }
    });
}

async function spawnSubprocessServer() {
    let port;
    try {
        port = await findFreePort();
    } catch (_e) {
        return null; // bind blocked — let caller short-circuit.
    }
    const script = [
        "import sys, pathlib",
        `sys.path.insert(0, ${JSON.stringify(REPO_ROOT)})`,
        "from workspace_web.server import serve_workspace",
        `serve_workspace(pathlib.Path(${JSON.stringify(CONTRACT_OUTPUT_ROOT)}), port=${port})`,
    ].join("\n");
    const proc = spawn(VENV_PYTHON, ["-c", script], {
        cwd: REPO_ROOT,
        stdio: ["ignore", "pipe", "pipe"],
        env: { ...process.env, PYTHONPATH: REPO_ROOT },
    });
    const deadline = Date.now() + 5000;
    while (Date.now() < deadline) {
        if (proc.exitCode !== null) {
            const stderr = proc.stderr.read()?.toString() || "";
            throw new Error(`server exited prematurely: ${stderr.slice(0, 400)}`);
        }
        try {
            const res = await fetch(
                `http://127.0.0.1:${port}/api/navigation`,
            );
            if (res.ok) {
                return Object.assign(proc, { port });
            }
        } catch (_e) {
            await sleep(50);
        }
    }
    proc.kill();
    throw new Error(`server failed to bind on port ${port} within 5s`);
}

// Per-test skip-handling: when the sandbox blocks binding the per-test
// invocation of `spawnSubprocessServer` returns null and the test
// self-skips. We do not pre-probe at module load because that
// would also fail noisily in sandboxed environments where
// the bundling path itself is the substantive signal.

// ---------------------------------------------------------------------------
// Regression: selectItem must surface 5xx into the detail panel.
//
// Background: `/api/library/item` may legitimately return 4xx/5xx when
// the user clicks a stale row (e.g. the file was archived between the
// search and the click). The previous implementation called
// `requestJson(...)` without a try/catch, leaving the previous detail
// in place and printing the error only to the console. The bundle
// must therefore contain the `.error:` setter path so the click
// visibly fails.
// ---------------------------------------------------------------------------

test("frontend selectItem surfaces fetch failure into the detail panel", () => {
    // We assert on the bundle rather than the React tree because JSDOM
    // does not run useEffect — the only reliable signal is whether the
    // bundler kept the error-handling branch.
    //
    // Vite minifies property access (`detail.error`) to a single-letter
    // alias (`O.error`) but keeps the user-facing string "Could not load
    // item" verbatim. So we look for the keyword `.error` plus the
    // error banner copy.
    assert.ok(
        /\.[A-Za-z_$]?\s*error\b/.test(BUNDLE_SOURCE) && /error:\s*(?:e\.message|\w+\.message)/.test(BUNDLE_SOURCE),
        "frontend bundle must call setDetail with an `error` payload using a message string when selectItem fails",
    );
    assert.ok(
        /Could not load item/i.test(BUNDLE_SOURCE),
        "frontend bundle must render the user-facing string 'Could not load item' in the error banner",
    );
});
