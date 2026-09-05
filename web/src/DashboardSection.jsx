import { startTransition, useEffect, useState } from "react";
import { useAutoRefresh } from "./autoRefresh.react.js";
import { requestJson } from "./api.js";
import DailyDiscoveryCard from "./DailyDiscoveryCard.jsx";
import { PagePurposeCard, PollErrorBanner } from "./workspaceShared.jsx";

export function DashboardSection({ section, autoRefreshEnabled }) {
  const [overview, setOverview] = useState(null);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    requestJson("/api/dashboard").then((payload) => {
      startTransition(() => {
        setOverview(payload);
        setLoadError("");
      });
    }).catch((err) => {
      // Without this catch a 5xx leaves `overview = null` and the user
      // sees an infinite "Loading dashboard…" shimmer — which looks like
      // a hang. Surface the error inline instead.
      startTransition(() => setLoadError(err.message || String(err)));
    });
  }, []);

  // Auto-refresh: re-fetch the dashboard on the polling interval. The form
  // state for this section is just the in-flight `overview` payload — refreshing
  // it does not affect the user's other inputs.
  const { lastError, dismissError } = useAutoRefresh({
    section: "dashboard",
    enabled: Boolean(autoRefreshEnabled),
    fetcher: () => requestJson("/api/dashboard"),
    onData: (_section, payload) => {
      startTransition(() => {
        setOverview(payload);
        setLoadError("");
      });
    },
  });

  if (loadError) {
    return (
      <section className="panel" role="status">
        <p className="eyebrow">Local archive</p>
        <h2>Could not load dashboard</h2>
        <p className="status-banner error" role="status">{loadError}</p>
        <p className="supporting">
          Make sure you launched this with <code>uv run research web</code> and that the
          <code> output/ </code> directory exists.
        </p>
      </section>
    );
  }
  if (!overview) {
    return <section className="panel shimmer">Loading dashboard…</section>;
  }

  return (
    <section className="panel dashboard-grid">
      <PollErrorBanner error={lastError} onDismiss={dismissError} />
      <PagePurposeCard section={section} />
      {overview.empty_state ? (
        <div className="empty-state-panel" role="status">
          <p className="eyebrow">First-run guidance</p>
          <p className="empty-state-explanation">{overview.empty_state.explanation}</p>
          <ul className="plain-list">
            {overview.empty_state.next_steps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="hero-card">
        <p className="eyebrow">Local archive</p>
        <h2>{overview.total_items} research items</h2>
        <p>Dashboard, Library, and Briefing all read from the same local sidecar truth.</p>
      </div>

      <DailyDiscoveryCard />

      <div className="metric-card">
        <p className="eyebrow">Source coverage</p>
        <div className="source-list">
          {Object.entries(overview.source_counts).map(([source, count]) => (
            <div key={source} className="source-pill">
              <span>{source}</span>
              <strong>{count}</strong>
            </div>
          ))}
        </div>
      </div>

      {overview.missing_sources.length ? (
        <details className="metric-card">
          <summary>
            <span className="eyebrow">Coverage gaps</span>
            <span className="muted"> — {overview.missing_sources.length} source(s) requested but empty</span>
          </summary>
          <ul className="plain-list">
            {overview.missing_sources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        </details>
      ) : null}

      {overview.recent_briefings.length ? (
        <div className="metric-card wide">
          <p className="eyebrow">Recent briefings</p>
          <ul className="plain-list">
            {overview.recent_briefings.map((entry) => (
              <li key={entry.path}>
                <strong>{entry.title}</strong>
                <span className="muted">{entry.path}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {overview.orphan_markdown_paths.length ? (
        <details className="metric-card wide">
          <summary>
            <span className="eyebrow">Orphan markdown</span>
            <span className="muted"> — {overview.orphan_markdown_paths.length} file(s) without a sidecar</span>
          </summary>
          <p className="muted">
            Run <code>uv run research backfill output</code> to generate sidecars from these files.
          </p>
          <ul className="plain-list compact">
            {overview.orphan_markdown_paths.map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
