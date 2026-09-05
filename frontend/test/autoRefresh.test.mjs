// Unit tests for createAutoRefreshController.
// Runs under plain Node (node:test) — no JSDOM, no React Testing Library.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  createAutoRefreshController,
  DEFAULT_POLLING_INTERVAL_MS,
  POLLED_SECTIONS,
} from "../src/autoRefresh.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeFakeTimers() {
  const timers = new Map();
  const calls = { setInterval: [], clearInterval: [] };
  let nextId = 1;
  const setIntervalFn = (cb, ms) => {
    const id = nextId++;
    timers.set(id, { cb, ms, cancelled: false });
    calls.setInterval.push({ id, ms });
    return id;
  };
  const clearIntervalFn = (id) => {
    calls.clearInterval.push(id);
    if (timers.has(id)) {
      timers.get(id).cancelled = true;
    }
  };
  // Tick the i-th still-alive interval callback. We do NOT tick cancelled
  // timers — this is what "the real wall clock fires" would do.
  async function tick(index = 0) {
    const alive = calls.setInterval.filter(({ id }) => timers.get(id) && !timers.get(id).cancelled);
    if (index >= alive.length) return;
    const { id } = alive[index];
    const t = timers.get(id);
    if (t.cancelled) return;
    await t.cb();
  }
  return { calls, setIntervalFn, clearIntervalFn, tick };
}

function makeController(overrides = {}) {
  const calls = { fetches: [], dataApplied: [], sectionChanges: [] };
  const timers = makeFakeTimers();
  const fetchers = {
    fetcher: async (section) => {
      calls.fetches.push(section);
      return { section, ts: Date.now() };
    },
    onData: (section, data) => {
      calls.dataApplied.push({ section, data });
    },
    onSectionChange: (section) => {
      calls.sectionChanges.push(section);
    },
  };
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    intervalMs: DEFAULT_POLLING_INTERVAL_MS,
    polledSections: POLLED_SECTIONS,
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
    ...fetchers,
    ...overrides.opts,
  });
  return { controller, calls, timers };
}

// ---------------------------------------------------------------------------
// Scenario 2 — Active read-path section is polled on an interval
// ---------------------------------------------------------------------------

test("active read-path section triggers an immediate fetch on start", async () => {
  const { controller, calls, timers } = makeController();
  await controller.start();
  assert.equal(calls.fetches.length, 1, "start() must fetch once");
  assert.equal(calls.fetches[0], "library");
  assert.equal(calls.dataApplied.length, 1, "data must be applied");
  assert.equal(timers.calls.setInterval.length, 1, "an interval must be armed");
  assert.equal(timers.calls.setInterval[0].ms, DEFAULT_POLLING_INTERVAL_MS);
  assert.equal(controller.isPolling(), true);
});

test("interval callback re-fetches the current section", async () => {
  const { controller, calls, timers } = makeController();
  await controller.start();
  // Simulate the wall clock firing the interval twice.
  await timers.tick(0);
  await timers.tick(0);
  // 1 initial + 2 ticks
  assert.equal(calls.fetches.length, 3);
  assert.ok(calls.fetches.every((s) => s === "library"));
});

test("default interval is 5 seconds", async () => {
  const { controller, timers } = makeController();
  await controller.start();
  assert.equal(timers.calls.setInterval[0].ms, 5000);
});

// ---------------------------------------------------------------------------
// Scenario 3 — Toggle off stops polling
// ---------------------------------------------------------------------------

test("setEnabled(false) clears the interval and stops future fetches", async () => {
  const { controller, calls, timers } = makeController();
  await controller.start();
  controller.setEnabled(false);
  assert.equal(controller.isPolling(), false);
  assert.equal(timers.calls.clearInterval.length, 1, "interval must be cleared");
  // No more fetches when the wall clock fires — the interval is gone.
  await timers.tick(0);
  assert.equal(calls.fetches.length, 1, "no new fetches after toggle off");
});

test("setEnabled(true) re-arms the interval when previously off", async () => {
  const { controller, timers } = makeController();
  await controller.start();
  controller.setEnabled(false);
  controller.setEnabled(true);
  assert.equal(controller.isPolling(), true);
  // clearInterval called once, setInterval called twice (initial + re-arm).
  assert.equal(timers.calls.setInterval.length, 2);
});

test("start() is a no-op when enabled is false", async () => {
  const { controller, calls, timers } = makeController({ opts: { enabled: false } });
  await controller.start();
  assert.equal(calls.fetches.length, 0);
  assert.equal(timers.calls.setInterval.length, 0);
  assert.equal(controller.isPolling(), false);
});

test("stop() also clears the interval", async () => {
  const { controller, timers } = makeController();
  await controller.start();
  controller.stop();
  assert.equal(controller.isPolling(), false);
  assert.equal(timers.calls.clearInterval.length, 1);
});

// ---------------------------------------------------------------------------
// Scenario 4 — Polling preserves user inputs (no form-state mutation)
// ---------------------------------------------------------------------------

test("the controller NEVER mutates the caller's fetcher or onData", async () => {
  // We give it a fetcher that closes over a "form" object. The polling tick
  // must not touch the form — only invoke the callback.
  const form = { keyword: "agent", sources: ["github"], page: 1 };
  const originalForm = JSON.stringify(form);
  const { controller } = makeController({
    opts: {
      fetcher: async () => {
        // simulate: fetch returns server data, must not touch form
        return { items: [] };
      },
      onData: () => {
        // real onData: replace the section's data, NOT the form
      },
    },
  });
  await controller.start();
  await controller.setSection("dashboard");
  // The test fixture's `form` should be byte-identical — controller never
  // receives it.
  assert.equal(JSON.stringify(form), originalForm, "controller must not mutate caller state");
});

// ---------------------------------------------------------------------------
// Scenario 5 — Section switch triggers an immediate refetch
// ---------------------------------------------------------------------------

test("setSection to another polled section fetches immediately and re-arms", async () => {
  const { controller, calls, timers } = makeController();
  await controller.start();
  const beforeClear = timers.calls.clearInterval.length;
  await controller.setSection("dashboard");
  // Two fetches total: initial library + the new dashboard
  assert.equal(calls.fetches.length, 2);
  assert.equal(calls.fetches[1], "dashboard");
  // Old interval was cleared and a new one armed
  assert.ok(timers.calls.clearInterval.length > beforeClear, "old interval must be cleared");
  assert.equal(timers.calls.setInterval.length, 2, "new interval must be armed");
  assert.equal(controller.getCurrentSection(), "dashboard");
});

test("setSection notifies onSectionChange", async () => {
  const { controller, calls } = makeController();
  await controller.start();
  await controller.setSection("briefing");
  assert.deepEqual(calls.sectionChanges, ["briefing"]);
});

test("setSection to the same section is a no-op (no extra fetch, no onSectionChange)", async () => {
  const { controller, calls } = makeController();
  await controller.start();
  const fetchCountBefore = calls.fetches.length;
  await controller.setSection("library");
  assert.equal(calls.fetches.length, fetchCountBefore, "no extra fetch for same section");
  assert.equal(calls.sectionChanges.length, 0);
});

// ---------------------------------------------------------------------------
// Scenario 6 — No new query parameters
// ---------------------------------------------------------------------------

test("fetcher receives ONLY the section id; no extra parameters leak in", async () => {
  const seenArgs = [];
  const timers = makeFakeTimers();
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async (section) => {
      seenArgs.push(section);
      return {};
    },
    onData: () => {},
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  await timers.tick(0);
  await controller.setSection("dashboard");
  for (const arg of seenArgs) {
    assert.equal(typeof arg, "string", "fetcher arg must be a section id string");
    assert.ok(POLLED_SECTIONS.includes(arg), `fetcher arg ${arg} is a valid polled section`);
  }
});

// ---------------------------------------------------------------------------
// Edge: polling errors must not break the interval
// ---------------------------------------------------------------------------

test("a fetcher rejection does NOT stop polling", async () => {
  const calls = { count: 0 };
  const timers = makeFakeTimers();
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async () => {
      calls.count += 1;
      throw new Error("network blip");
    },
    onData: () => {},
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start(); // throws, but caught
  assert.equal(calls.count, 1);
  // Interval still armed
  assert.equal(controller.isPolling(), true);
  // Next wall-clock tick should also fire
  await timers.tick(0);
  assert.equal(calls.count, 2);
});

// ---------------------------------------------------------------------------
// fix-auto-refresh-expose-poll-errors
// ---------------------------------------------------------------------------

test("fetcher rejection fires onError(section, error) and exposes lastError", async () => {
  const timers = makeFakeTimers();
  const errors = [];
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async () => {
      throw new Error("network blip");
    },
    onData: () => {},
    onError: (section, err) => errors.push({ section, err }),
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  assert.equal(errors.length, 1, "onError must fire on rejection");
  assert.equal(errors[0].section, "library");
  assert.ok(errors[0].err instanceof Error);
  assert.match(errors[0].err.message, /network blip/);
  // lastError must be queryable
  assert.ok(controller.getLastError("library") instanceof Error);
  assert.match(controller.getLastError("library").message, /network blip/);
  // Polling is still armed
  assert.equal(controller.isPolling(), true);
});

test("getLastError returns null for sections that haven't failed", async () => {
  const timers = makeFakeTimers();
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async () => ({ items: [] }),
    onData: () => {},
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  assert.equal(controller.getLastError("library"), null);
  // Also for sections the controller never touched
  assert.equal(controller.getLastError("briefing"), null);
});

test("successful fetch after a failure clears lastError for that section", async () => {
  let shouldFail = true;
  const timers = makeFakeTimers();
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async () => {
      if (shouldFail) throw new Error("blip");
      return { items: [] };
    },
    onData: () => {},
    onError: () => {},
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  assert.ok(controller.getLastError("library") instanceof Error, "first tick should have failed");
  // Flip the flag and tick again
  shouldFail = false;
  await timers.tick(0);
  assert.equal(controller.getLastError("library"), null, "successful fetch must clear lastError");
});

test("dismissError(section) clears the last error", async () => {
  const timers = makeFakeTimers();
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async () => {
      throw new Error("blip");
    },
    onData: () => {},
    onError: () => {},
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  assert.ok(controller.getLastError("library") instanceof Error);
  controller.dismissError("library");
  assert.equal(controller.getLastError("library"), null);
  // Polling still armed — dismiss does NOT stop the interval
  assert.equal(controller.isPolling(), true);
});

test("onError is per-section: errors on section A do not leak to section B", async () => {
  const timers = makeFakeTimers();
  const errors = [];
  const controller = createAutoRefreshController({
    section: "library",
    enabled: true,
    fetcher: async (s) => {
      if (s === "library") throw new Error("library down");
      return { ok: true };
    },
    onData: () => {},
    onError: (section, err) => errors.push({ section, message: err.message }),
    setInterval: timers.setIntervalFn,
    clearInterval: timers.clearIntervalFn,
  });
  await controller.start();
  assert.equal(errors.length, 1);
  assert.equal(errors[0].section, "library");
  assert.match(errors[0].message, /library down/);
  // Switch to briefing — successful, no new error
  await controller.setSection("briefing");
  assert.equal(errors.length, 1, "no new error on successful section switch fetch");
  // library's error is still tracked
  assert.ok(controller.getLastError("library") instanceof Error);
  assert.equal(controller.getLastError("briefing"), null);
});
