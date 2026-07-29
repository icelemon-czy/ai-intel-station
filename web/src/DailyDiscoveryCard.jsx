import { useCallback, useEffect, useState } from "react";
import { requestJson } from "./api.js";

/**
 * DailyDiscoveryCard — a user-friendly trigger for the daily discovery sweep.
 *
 * Design goals:
 *   1. Always tell the user what's happening and what to do next.
 *   2. Surface every per-source result so users can spot partial failures.
 *   3. Provide clickable links to the actual briefing markdown.
 *   4. Recover gracefully from errors with an actionable next step.
 *   5. Stay responsive on small viewports (no horizontal scroll).
 */
export default function DailyDiscoveryCard() {
  const [status, setStatus] = useState({ kind: "loading" });
  const [job, setJob] = useState(null); // { id, phase, result }
  const [showHints, setShowHints] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const payload = await requestJson("/api/discover/status");
      setStatus({ kind: "ready", data: payload });
    } catch (err) {
      setStatus({ kind: "error", message: err.message || String(err) });
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Poll a running job until it terminates.
  useEffect(() => {
    if (!job || job.phase !== "running") return undefined;
    let cancelled = false;
    const tick = async () => {
      while (!cancelled) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        if (cancelled) return;
        try {
          const record = await requestJson(`/api/discover/job?id=${encodeURIComponent(job.id)}`);
          if (!record || record.status !== "running") {
            setJob(record ? { id: job.id, phase: "done", result: record.result, status: record.status } : { id: job.id, phase: "done", result: null, status: "unknown" });
            refresh();
            return;
          }
        } catch (err) {
          setJob({ id: job.id, phase: "error", message: err.message || String(err) });
          refresh();
          return;
        }
      }
    };
    tick();
    return () => {
      cancelled = true;
    };
  }, [job, refresh]);

  const runNow = useCallback(async () => {
    setJob({ id: null, phase: "starting" });
    try {
      const payload = await requestJson("/api/discover/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (payload && payload.job_id) {
        setJob({ id: payload.job_id, phase: "running" });
      } else if (payload && payload.status === "config_error") {
        setJob({ phase: "done", status: "config_error", result: { message: payload.message } });
      } else {
        setJob({ phase: "error", message: "Unexpected response from server" });
      }
    } catch (err) {
      setJob({ phase: "error", message: err.message || String(err) });
    }
  }, []);

  const cancelJob = useCallback(() => {
    // Best-effort: the server can't actually cancel an in-flight run, but we
    // can stop polling so the UI is responsive. The next refresh will show
    // whatever state the job ended up in.
    setJob(null);
    refresh();
  }, [refresh]);

  const isRunning = job?.phase === "starting" || job?.phase === "running";

  return (
    <section className="discovery-card" aria-labelledby="discovery-heading">
      <header className="discovery-card-header">
        <p className="eyebrow">Daily discovery</p>
        <h2 id="discovery-heading" className="discovery-card-title">
          Collect GitHub, arXiv, and WeChat — automatically
        </h2>
        <p className="discovery-card-subtitle">
          Runs the configured sources, then writes a digest into{" "}
          <code>output/briefing/</code>. No more manual <code>research collect</code> every morning.
        </p>
      </header>

      <StatusBlock status={status} onRetry={refresh} />

      {job ? <JobTimeline job={job} /> : null}

      <div className="discovery-actions">
        <button
          type="button"
          className="primary"
          onClick={runNow}
          disabled={isRunning}
          aria-busy={isRunning}
        >
          {isRunning ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Running…
            </>
          ) : (
            "Run daily discovery now"
          )}
        </button>
        {isRunning ? (
          <button type="button" className="secondary" onClick={cancelJob}>
            Stop polling
          </button>
        ) : (
          <button type="button" className="secondary" onClick={refresh}>
            Refresh status
          </button>
        )}
      </div>

      <FirstRunHint
        status={status}
        hasJob={Boolean(job)}
        forceVisible={showHints}
      />
      {!showHints && status.kind === "ready" && status.data?.has_run ? (
        <button
          type="button"
          className="discovery-secondary-link"
          onClick={() => setShowHints(true)}
        >
          Show setup hints again
        </button>
      ) : null}
    </section>
  );
}

export function StatusBlock({ status, onRetry }) {
  if (status.kind === "loading") {
    return (
      <div className="discovery-status-row" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <span className="muted">Checking last run…</span>
      </div>
    );
  }
  if (status.kind === "error") {
    return (
      <div className="discovery-status-row discovery-error" role="alert">
        <div>
          <strong>Could not read status:</strong>{" "}
          <span className="muted">{status.message}</span>
        </div>
        {onRetry ? (
          <button type="button" className="secondary" onClick={onRetry}>
            Retry
          </button>
        ) : null}
        <p className="muted">
          The latest log file in{" "}
          <code>.state/discovery/</code> still has the most recent run
          details.
        </p>
      </div>
    );
  }
  const data = status.data || {};
  if (!data.has_run) {
    return (
      <div className="discovery-status-row">
        <strong>No runs yet.</strong>{" "}
        <span className="muted">
          When you click <em>Run daily discovery now</em> (or wait for the schedule), the
          result will appear here.
        </span>
      </div>
    );
  }
  return (
    <dl className="discovery-summary">
      <dt>Last run</dt>
      <dd>{data.started_at || "unknown"}</dd>
      {data.summary ? (
        <>
          <dt>Result</dt>
          <dd>{data.summary}</dd>
        </>
      ) : null}
      {data.briefing ? (
        <>
          <dt>Briefing</dt>
          <dd className="discovery-briefing-link">
            {data.briefing.path ? (
              <a
                href={`/${encodeURI(data.briefing.path)}`}
                target="_blank"
                rel="noreferrer"
              >
                {data.briefing.path} ↗
              </a>
            ) : (
              <span className="muted">{data.briefing.path || "(none)"}</span>
            )}
            {" "}
            <span className="muted">({data.briefing.item_count ?? "?"} items)</span>
          </dd>
        </>
      ) : null}
    </dl>
  );
}

export function JobTimeline({ job }) {
  const { phase, result, status, message } = job;
  if (phase === "starting") {
    return (
      <div className="job-timeline" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <span>Starting job on the server…</span>
      </div>
    );
  }
  if (phase === "running") {
    return (
      <div className="job-timeline" role="status" aria-live="polite">
        <span className="spinner" aria-hidden="true" />
        <span>
          Sweep in progress. This polls every 1.5s — feel free to keep the tab open or close it
          and come back; the result will be in the log on disk.
        </span>
      </div>
    );
  }
  if (phase === "error") {
    return (
      <div className="job-timeline job-error" role="alert">
        <strong>Could not start the job.</strong>
        <div className="muted">{message}</div>
        <RecoveryHints />
      </div>
    );
  }
  // done
  if (status === "config_error") {
    return (
      <div className="job-timeline job-error" role="alert">
        <strong>Configuration error.</strong>
        <div className="muted">
          {result?.message || "The discovery YAML has a problem."} Run{" "}
          <code>uv run research discover --dry-run</code> for a detailed report.
        </div>
        <RecoveryHints />
      </div>
    );
  }
  if (!result || !result.sources) {
    return (
      <div className="job-timeline job-error" role="alert">
        <strong>Job finished but produced no report.</strong>
        <RecoveryHints />
      </div>
    );
  }
  return <ResultReport result={result} />;
}

export function ResultReport({ result }) {
  const entries = Object.entries(result.sources || {});
  return (
    <div className="job-timeline job-done" role="status">
      <strong>
        {result.status === "ok" ? "All sources succeeded." : "Sweep finished with some failures."}
      </strong>
      <table className="job-table" aria-label="Per-source results">
        <thead>
          <tr>
            <th scope="col">Source</th>
            <th scope="col">Succeeded</th>
            <th scope="col">Skipped</th>
            <th scope="col">Failed</th>
            <th scope="col">Notes</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(([name, info]) => (
            <tr key={name}>
              <th scope="row">{name}</th>
              <td>{info.succeeded}</td>
              <td>{info.skipped}</td>
              <td className={info.failed ? "job-fail" : ""}>{info.failed}</td>
              <td className="muted job-notes">
                {(info.notes || []).slice(0, 3).join(" · ") || "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {result.briefing && result.briefing.path && result.briefing.path !== "(dry-run)" ? (
        <p>
          📰 Briefing saved:{" "}
          <a
            href={`/${encodeURI(result.briefing.path)}`}
            target="_blank"
            rel="noreferrer"
          >
            {result.briefing.path}
          </a>{" "}
          <span className="muted">({result.briefing.item_count} items)</span>
        </p>
      ) : null}
    </div>
  );
}

export function FirstRunHint({ status, hasJob, forceVisible = false }) {
  // Only show on first run, before any job has been kicked off, unless the
  // user explicitly asked to re-show hints via the "Show setup hints again"
  // button.
  if (!forceVisible && (status.kind !== "ready" || status.data?.has_run || hasJob)) return null;
  return (
    <details className="discovery-first-run-hint">
      <summary>First time here? Read this.</summary>
      <ol>
        <li>
          On the command line, run <code>uv run research init-config</code> to write{" "}
          <code>config/discovery.yaml</code>.
        </li>
        <li>
          Edit that file — pick the GitHub repos and arXiv categories you care about.
        </li>
        <li>
          Run <code>uv run research discover --dry-run</code> to preview what would happen
          with no network calls.
        </li>
        <li>
          Once it looks right, run <code>uv run research schedule launchd --install</code> so
          this card becomes unnecessary.
        </li>
      </ol>
    </details>
  );
}

export function RecoveryHints() {
  return (
    <ul className="muted recovery-list">
      <li>
        Run <code>uv run research discover --dry-run</code> to see what would have happened.
      </li>
      <li>
        Check <code>.state/discovery/</code> for the latest log file.
      </li>
      <li>
        If the YAML is wrong, edit <code>config/discovery.yaml</code> and try again.
      </li>
    </ul>
  );
}
