import { startTransition, useEffect, useState } from "react";
import { useAutoRefresh } from "./autoRefresh.react.js";
import { requestJson } from "./api.js";
import { PagePurposeCard, PollErrorBanner } from "./workspaceShared.jsx";

function buildCollectFieldDefaults(fields) {
  return Object.fromEntries(
    fields.map((field) => [field.name, field.default ?? (field.type === "boolean" ? false : "")]),
  );
}

export function CollectSection({ section, autoRefreshEnabled, setActiveSection }) {
  const [sources, setSources] = useState([]);
  const [activeSource, setActiveSource] = useState("github");
  const [formDefinition, setFormDefinition] = useState(null);
  const [fieldValues, setFieldValues] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    requestJson("/api/collect/sources").then((payload) => {
      startTransition(() => {
        setSources(payload);
        if (payload[0]?.id) {
          setActiveSource(payload[0].id);
        }
      });
    }).catch((err) => {
      // Without this catch a 5xx leaves `sources = []` and the user
      // sees a form they cannot switch sources on — silent and confusing.
      startTransition(() => setErrorMessage(`Could not load source list: ${err.message || err}`));
    });
  }, []);

  // Auto-refresh: re-fetch the collect sources list so the user sees a new
  // source type if/when one is added server-side. We do NOT touch
  // `activeSource`, `formDefinition`, `fieldValues`, or `result` — those are
  // user-controlled state.
  const { lastError: collectLastError, dismissError: collectDismissError } = useAutoRefresh({
    section: "collect",
    enabled: Boolean(autoRefreshEnabled),
    fetcher: () => requestJson("/api/collect/sources"),
    onData: (_section, payload) => {
      startTransition(() => {
        setSources(payload);
      });
    },
  });

  useEffect(() => {
    requestJson(`/api/collect/form/${activeSource}`).then((payload) => {
      startTransition(() => {
        setFormDefinition(payload);
        setFieldValues(buildCollectFieldDefaults(payload.fields || []));
        setResult(null);
        setErrorMessage((current) => current && current.startsWith("Could not load source list") ? current : "");
      });
    }).catch((err) => {
      // Surface the failure so the user can see why the form is empty.
      startTransition(() => setErrorMessage(`Could not load form for ${activeSource}: ${err.message || err}`));
    });
  }, [activeSource]);

  function updateField(name, value) {
    setFieldValues((current) => ({ ...current, [name]: value }));
  }

  async function runCollect(event) {
    event?.preventDefault();
    setLoading(true);
    setErrorMessage("");
    try {
      const payload = await requestJson("/api/collect/run", {
        method: "POST",
        body: JSON.stringify({ source: activeSource, fields: fieldValues }),
      });
      startTransition(() => {
        setResult(payload);
        setLoading(false);
      });
    } catch (error) {
      startTransition(() => {
        setResult(null);
        setErrorMessage(error.message);
        setLoading(false);
      });
    }
  }

  return (
    <section className="collect-layout">
      <PollErrorBanner error={collectLastError} onDismiss={collectDismissError} />
      <PagePurposeCard section={section} />
      <form className="panel collect-panel" onSubmit={runCollect}>
        <p className="eyebrow">Collect workspace</p>
        <h2>{formDefinition?.label || activeSource}</h2>
        <p className="supporting">{formDefinition?.description || "Choose a source and run a manual collection."}</p>

        {!result ? (
          <div className="empty-state-panel collect-emptyState" role="status">
            <p className="eyebrow">First time here?</p>
            <p className="empty-state-explanation">
              Pick a source, fill the inputs below, then press <strong>Run now</strong>.
              Collected items land in <code>output/&lt;source&gt;/</code> and become
              searchable from the Library.
            </p>
          </div>
        ) : null}

        <div>
          <span className="field-label">Source</span>
          <div className="source-list">
            {sources.map((source) => (
              <button
                key={source.id}
                type="button"
                className={`source-switch ${source.id === activeSource ? "active" : ""}`}
                onClick={() => setActiveSource(source.id)}
              >
                {source.label}
              </button>
            ))}
          </div>
        </div>

        {/* Dependency hint shown prominently so users see prerequisites
            BEFORE clicking Run — not after a 500 error. */}
        {formDefinition?.dependency_hint ? (
          <div className="dependency-banner" role="note">
            <strong>Prerequisite:</strong>{" "}
            <span className="muted">{formDefinition.dependency_hint}</span>
          </div>
        ) : null}

        {formDefinition ? (
          <details className="purpose-card" aria-label={`${formDefinition.label} purpose`}>
            <summary>
              <span className="eyebrow">What this source is for</span>
              <span className="muted"> — {formDefinition.purpose}</span>
            </summary>
            <dl className="purpose-grid">
              <div>
                <dt>Required input</dt>
                <dd>{formDefinition.required_input}</dd>
              </div>
              <div>
                <dt>Local output</dt>
                <dd><code>{formDefinition.output_dir}</code></dd>
              </div>
              <div>
                <dt>Dependency hint</dt>
                <dd>{formDefinition.dependency_hint || "none"}</dd>
              </div>
            </dl>
          </details>
        ) : null}

        {formDefinition?.fields?.map((field) => {
          if (field.type === "boolean") {
            return (
              <label key={field.name} className="inline-toggle">
                <input
                  type="checkbox"
                  checked={Boolean(fieldValues[field.name])}
                  onChange={(event) => updateField(field.name, event.target.checked)}
                />
                <div>
                  <strong>{field.label}</strong>
                  <p className="supporting">{field.description || "Toggle this option for the current source."}</p>
                </div>
              </label>
            );
          }

          return (
            <label key={field.name}>
              {field.label}
              <input
                type={field.type === "number" ? "number" : "text"}
                value={fieldValues[field.name] ?? ""}
                placeholder={field.placeholder || ""}
                onChange={(event) => updateField(field.name, event.target.value)}
              />
            </label>
          );
        })}

        <div className="action-row">
          <button type="submit">{loading ? "Running collection…" : "Run now"}</button>
          <div className="collect-mode-note">
            <span className="field-label">Execution mode</span>
            <p className="supporting">Manual run only</p>
          </div>
        </div>
      </form>

      <div className="collect-sidecar">
        <div className="panel collect-result-panel">
          <p className="eyebrow">Run status</p>
          {errorMessage ? <p className="status-banner error">{errorMessage}</p> : null}
          {result?.summary ? <p className={`status-banner ${result.status || "pending"}`}>{result.summary}</p> : null}
          {result?.next_step ? <p className="supporting">{result.next_step}</p> : null}
          {result?.status === "success" ? (
            <button type="button" className="cta-button" onClick={() => setActiveSection("library")}>
              Go to Library to view collected items
            </button>
          ) : null}
          {loading ? <p>Collecting with the local runtime…</p> : null}
          {result ? (
            <details className="collect-technical-details">
              <summary>Technical details</summary>
              <pre className="json-preview">{JSON.stringify(result, null, 2)}</pre>
            </details>
          ) : null}
        </div>

        <div className="panel collect-result-panel">
          <p className="eyebrow">What is not here yet</p>
          <ul className="plainList compact-list">
            <li>Queued / running / failed job history timeline</li>
            <li>Scheduled collection and refresh policy controls</li>
            <li>Dashboard freshness badges fed by the jobs layer</li>
          </ul>
        </div>
      </div>
    </section>
  );
}
