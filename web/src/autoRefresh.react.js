// React hook wrapper around the pure-JS `createAutoRefreshController`.
//
// Kept in a separate file so `autoRefresh.js` (the pure factory + constants)
// can be unit-tested under plain Node without pulling in React. Vite will
// tree-shake this file when the entry point only imports the pure helpers.

import { useEffect, useRef, useState } from "react";
import { createAutoRefreshController } from "./autoRefresh.js";

/**
 * React hook: tie `createAutoRefreshController` to a section + enabled flag.
 *
 * The fetcher / onData / onError / onSectionChange callbacks are stored in
 * refs so the caller does not need to memoise them — the controller dispatches
 * via the latest ref values on each tick.
 *
 * Returns the current `lastError` (or null) and a `dismissError()` callback
 * so the caller can render an error banner. `forceUpdate` is exposed as a
 * stability escape hatch — not currently used by App.jsx.
 *
 * @param {object} opts
 * @param {string} opts.section
 * @param {boolean} opts.enabled
 * @param {(section: string) => Promise<any>} opts.fetcher
 * @param {(section: string, data: any) => void} opts.onData
 * @param {(section: string) => void} [opts.onSectionChange]
 */
export function useAutoRefresh({ section, enabled, fetcher, onData, onSectionChange }) {
  const fetcherRef = useRef(fetcher);
  const onDataRef = useRef(onData);
  const onSectionChangeRef = useRef(onSectionChange);
  fetcherRef.current = fetcher;
  onDataRef.current = onData;
  onSectionChangeRef.current = onSectionChange;

  // The last error for THIS hook's section, plus a monotonic counter to
  // force a re-render when onError fires. We track the counter separately
  // because storing the Error object as state would cause a re-render even
  // when the caller already keeps its own `lastError` state.
  const [lastError, setLastError] = useState(null);
  // Track which error we've already surfaced as state to avoid stale
  // overwrites when the user re-mounts or section-changes.
  const surfacedErrorRef = useRef(null);

  const controllerRef = useRef(null);
  if (controllerRef.current === null) {
    controllerRef.current = createAutoRefreshController({
      section,
      enabled,
      fetcher: (s) => fetcherRef.current(s),
      onData: (s, data) => onDataRef.current(s, data),
      onError: (s, err) => {
        // Only forward errors for OUR section — section switches should not
        // surface errors from the previous section to this hook's UI.
        if (s === controllerRef.current.getCurrentSection()) {
          surfacedErrorRef.current = err;
          setLastError(err);
        }
      },
      onSectionChange: (s) => {
        if (onSectionChangeRef.current) onSectionChangeRef.current(s);
      },
    });
  }

  useEffect(() => {
    const controller = controllerRef.current;
    controller.setEnabled(enabled);
    if (enabled) {
      controller.start();
    } else {
      controller.stop();
    }
    return () => controller.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);

  useEffect(() => {
    const controller = controllerRef.current;
    // Section changed: clear any prior error for THIS hook.
    surfacedErrorRef.current = null;
    setLastError(null);
    controller.setSection(section);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [section]);

  function dismissError() {
    const controller = controllerRef.current;
    surfacedErrorRef.current = null;
    setLastError(null);
    controller.dismissError(section);
  }

  return { lastError, dismissError, _controller: controllerRef.current };
}
