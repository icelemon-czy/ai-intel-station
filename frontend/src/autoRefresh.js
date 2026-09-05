// Auto-refresh controller for the Web workspace read-path sections.
//
// This file is intentionally React-free. It exports a pure factory
// (`createAutoRefreshController`) plus constants. The React hook wrapper
// lives in `autoRefresh.react.js` and is what App.jsx consumes.
//
// The shape of the controller intentionally mirrors a React effect: caller
// passes in `setInterval` / `clearInterval` (so tests can pass fakes), and
// `onData(data)` / `onSectionChange(section)` callbacks. The controller does
// NOT touch any global state and does NOT mutate the caller's inputs.

export const DEFAULT_POLLING_INTERVAL_MS = 5000;

export const POLLED_SECTIONS = ["dashboard", "library", "briefing", "collect"];

/**
 * Build an auto-refresh controller.
 *
 * @param {object} opts
 * @param {string} opts.section - Active section id (one of POLLED_SECTIONS).
 * @param {boolean} opts.enabled - Whether polling is on.
 * @param {string[]} [opts.polledSections] - Override the polled section list (default POLLED_SECTIONS).
 * @param {number} [opts.intervalMs] - Override interval (default DEFAULT_POLLING_INTERVAL_MS).
 * @param {(section: string) => Promise<any>} opts.fetcher - Fetch data for the active section.
 * @param {(section: string, data: any) => void} opts.onData - Apply fetched data to section.
 * @param {(section: string) => void} [opts.onSectionChange] - Hook called on section switch.
 * @param {typeof setInterval} [opts.setInterval] - Injected timer.
 * @param {typeof clearInterval} [opts.clearInterval] - Injected timer.
 *
 * @returns {{
 *   start: () => Promise<void>,
 *   stop: () => void,
 *   setEnabled: (enabled: boolean) => void,
 *   setSection: (section: string) => Promise<void>,
 *   getCurrentSection: () => string,
 *   isPolling: () => boolean,
 * }}
 */
export function createAutoRefreshController(opts) {
  const {
    section: initialSection,
    enabled: initialEnabled,
    polledSections = POLLED_SECTIONS,
    intervalMs = DEFAULT_POLLING_INTERVAL_MS,
    fetcher,
    onData,
    onError,
    onSectionChange,
    setInterval: setIntervalFn = setInterval,
    clearInterval: clearIntervalFn = clearInterval,
  } = opts;

  if (!polledSections.includes(initialSection)) {
    throw new Error(
      `createAutoRefreshController: initial section ${JSON.stringify(initialSection)} is not in polledSections`,
    );
  }

  let currentSection = initialSection;
  let enabled = initialEnabled;
  let timer = null;
  let lastSectionBeforeStop = currentSection;
  // Per-section last error. Cleared by a successful fetch OR by dismissError().
  const lastErrors = new Map();

  function recordError(targetSection, err) {
    lastErrors.set(targetSection, err);
    if (onError) {
      try {
        onError(targetSection, err);
      } catch {
        // The caller's onError handler threw — do not let it kill polling.
      }
    }
  }

  function clearError(targetSection) {
    if (lastErrors.has(targetSection)) {
      lastErrors.delete(targetSection);
    }
  }

  function isPolling() {
    return timer !== null;
  }

  function getCurrentSection() {
    return currentSection;
  }

  function clearTimer() {
    if (timer !== null) {
      clearIntervalFn(timer);
      timer = null;
    }
  }

  async function runOnce(targetSection) {
    try {
      const data = await fetcher(targetSection);
      // Successful fetch — clear any prior error for this section.
      clearError(targetSection);
      onData(targetSection, data);
    } catch (err) {
      // Polling errors MUST NOT break the interval; the next tick retries.
      // We still surface the error via onError + lastErrors so the UI can
      // show "polling failed" without interrupting the user's work.
      recordError(targetSection, err);
    }
  }

  function startTimer() {
    if (!enabled) return;
    if (!polledSections.includes(currentSection)) return;
    if (timer !== null) return;
    timer = setIntervalFn(() => {
      runOnce(currentSection);
    }, intervalMs);
  }

  async function start() {
    lastSectionBeforeStop = currentSection;
    if (!enabled) return;
    if (!polledSections.includes(currentSection)) return;
    await runOnce(currentSection);
    startTimer();
  }

  function stop() {
    clearTimer();
  }

  function setEnabled(nextEnabled) {
    if (nextEnabled === enabled) return;
    enabled = nextEnabled;
    if (enabled) {
      startTimer();
    } else {
      clearTimer();
    }
  }

  async function setSection(nextSection) {
    if (nextSection === currentSection) {
      // Same section — keep polling, no special action.
      if (enabled && timer === null) {
        startTimer();
      }
      return;
    }
    const previousSection = currentSection;
    currentSection = nextSection;
    if (onSectionChange) {
      onSectionChange(nextSection);
    }
    if (!enabled) return;
    if (!polledSections.includes(nextSection)) {
      clearTimer();
      return;
    }
    // Switch: drop the old timer, fetch the new section once, then resume.
    clearTimer();
    await runOnce(nextSection);
    startTimer();
    // Suppress unused-var lint
    void previousSection;
    void lastSectionBeforeStop;
  }

  function getLastError(targetSection) {
    return lastErrors.get(targetSection) || null;
  }

  function dismissError(targetSection) {
    clearError(targetSection);
  }

  return {
    start,
    stop,
    setEnabled,
    setSection,
    getCurrentSection,
    isPolling,
    getLastError,
    dismissError,
    // Test-only escape hatch: lets SSR tests seed a fake error so they can
    // assert that the React surface actually surfaces it. Production code
    // should never read this — it is intentionally prefixed with `__`.
    __lastErrorsForTest: lastErrors,
  };
}
