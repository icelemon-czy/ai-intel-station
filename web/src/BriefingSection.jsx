import { startTransition, useEffect, useState } from "react";
import { useAutoRefresh } from "./autoRefresh.react.js";
import { requestJson } from "./api.js";
import { SOURCE_OPTIONS } from "./workspaceOptions.js";
import { PagePurposeCard, PollErrorBanner } from "./workspaceShared.jsx";

export function BriefingSection({ section, autoRefreshEnabled }) {
  const [form, setForm] = useState({ mode: "digest", keyword: "agent", title: "AI Agents", sources: ["github", "papers", "wechat"], since: "", until: "" });
  const [preview, setPreview] = useState("");
  const [savedPath, setSavedPath] = useState("");
  const [loading, setLoading] = useState(false);
  const [emptyState, setEmptyState] = useState(null);
  const [flowNotes, setFlowNotes] = useState({ input_source: "", preview_vs_save: "", saved_artifact: "" });
  const [modePurposes, setModePurposes] = useState({ digest: "", "reading-list": "" });
  const [actionPurposes, setActionPurposes] = useState({ preview: "", save: "" });

  useEffect(() => {
    requestJson("/api/briefing/metadata").then((payload) => {
      startTransition(() => {
        if (payload.flow_notes) setFlowNotes(payload.flow_notes);
        if (payload.mode_purposes) setModePurposes(payload.mode_purposes);
        if (payload.action_purposes) setActionPurposes(payload.action_purposes);
      });
    }).catch((err) => {
      // Without this catch, metadata fetches that 5xx leave the
      // briefing-copy state empty (default uplicate objects) — the user
      // sees no explainer text and the symptom is invisible to them.
      console.error("failed to load /api/briefing/metadata:", err);
    });
  }, []);

  // Auto-refresh: re-fetch briefing metadata every interval so flow notes and
  // mode / action purposes stay in sync with the backend. We do NOT touch
  // `preview`, `savedPath`, `loading`, or `form` — only metadata.
  const { lastError: briefingLastError, dismissError: briefingDismissError } = useAutoRefresh({
    section: "briefing",
    enabled: Boolean(autoRefreshEnabled),
    fetcher: () => requestJson("/api/briefing/metadata"),
    onData: (_section, payload) => {
      startTransition(() => {
        if (payload.flow_notes) setFlowNotes(payload.flow_notes);
        if (payload.mode_purposes) setModePurposes(payload.mode_purposes);
        if (payload.action_purposes) setActionPurposes(payload.action_purposes);
      });
    },
  });

  function updateField(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
  }

  function toggleSource(source) {
    setForm((current) => ({
      ...current,
      sources: current.sources.includes(source)
        ? current.sources.filter((item) => item !== source)
        : [...current.sources, source],
    }));
  }

  async function runAction(path) {
    setLoading(true);
    let payload;
    try {
      payload = await requestJson(path, {
        method: "POST",
        body: JSON.stringify(form),
      });
    } catch (err) {
      // Same pattern as LibrarySection.runSearch: without this catch
      // the spinner spins forever on a 5xx.
      startTransition(() => {
        setPreview("");
        setSavedPath("");
        setEmptyState({
          explanation: `Briefing failed: ${err.message || err}`,
          next_steps: ["Try a different keyword", "Re-check form inputs"],
        });
        setLoading(false);
      });
      return;
    }
    startTransition(() => {
      setPreview(payload.content);
      setSavedPath(payload.path || "");
      setEmptyState(payload.empty_state || null);
      setLoading(false);
    });
  }

  return (
    <section className="briefing-layout">
      <PollErrorBanner error={briefingLastError} onDismiss={briefingDismissError} />
      <PagePurposeCard section={section} />
      <div className="panel control-panel">
        <p className="eyebrow">Briefing workspace</p>
        <aside className="briefing-flow-note" aria-label="Briefing flow explanation">
          <p className="eyebrow">How briefing generation works</p>
          <p>{flowNotes.input_source}</p>
          <p>{flowNotes.preview_vs_save}</p>
        </aside>

        <label>
          Mode
          <select value={form.mode} onChange={(event) => updateField("mode", event.target.value)}>
            <option value="digest">digest</option>
            <option value="reading-list">reading-list</option>
          </select>
        </label>
        <p className="supporting">{modePurposes[form.mode] || ""}</p>
        <label>
          Keyword
          <input value={form.keyword} onChange={(event) => updateField("keyword", event.target.value)} />
        </label>
        <label>
          Title
          <input value={form.title} onChange={(event) => updateField("title", event.target.value)} />
        </label>

        <div>
          <span className="field-label">Sources</span>
          <div className="source-list">
            {SOURCE_OPTIONS.map((source) => (
              <label key={source} className={`source-toggle ${form.sources.includes(source) ? "active" : ""}`}>
                <input type="checkbox" checked={form.sources.includes(source)} onChange={() => toggleSource(source)} />
                <span>{source}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="action-row">
          <button type="button" onClick={() => runAction("/api/briefing/preview")}>Preview briefing</button>
          <button type="button" className="secondary" onClick={() => runAction("/api/briefing/save")}>Save to output/briefing</button>
        </div>
        <p className="supporting">{actionPurposes.preview}</p>
        <p className="supporting">{actionPurposes.save}</p>
        {loading ? <p>Working on local briefing…</p> : null}
        {savedPath ? (
          <p className="supporting">
            {flowNotes.saved_artifact} <strong>Saved: {savedPath}</strong>
          </p>
        ) : (
          <p className="supporting">Preview first, then save when the local result looks right.</p>
        )}
      </div>

      <div className="panel preview-panel">
        <p className="eyebrow">Markdown preview</p>
        {!preview && emptyState ? (
          <div className="empty-state-panel" role="status">
            <p className="eyebrow">No preview yet</p>
            <p className="empty-state-explanation">{emptyState.explanation}</p>
            <ul className="plainList">
              {emptyState.next_steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <pre>{preview || "Run preview to inspect the derived Markdown before saving."}</pre>
      </div>
    </section>
  );
}
