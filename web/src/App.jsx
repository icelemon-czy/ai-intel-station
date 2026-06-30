import { startTransition, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAutoRefresh } from "./autoRefresh.react.js";
import { requestJson } from "./api.js";
import DailyDiscoveryCard from "./DailyDiscoveryCard.jsx";

const SOURCE_OPTIONS = ["github", "papers", "wechat"];

function buildCollectFieldDefaults(fields) {
  return Object.fromEntries(
    fields.map((field) => [field.name, field.default ?? (field.type === "boolean" ? false : "")]),
  );
}

function CopyArchivePathButton({ outputPath }) {
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");

  async function handleCopy() {
    if (!outputPath) return;
    setError("");
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
        await navigator.clipboard.writeText(outputPath);
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      } else {
        setError("Clipboard API not available in this browser; please copy the path manually.");
      }
    } catch (err) {
      setError(err && err.message ? err.message : "Could not access the clipboard.");
    }
  }

  return (
    <div className="copy-archive-path">
      <button
        type="button"
        className="copy-archive-path-button"
        onClick={handleCopy}
        aria-label="Copy archive path to clipboard"
      >
        {copied ? "Copied" : "Copy archive path"}
      </button>
      {error ? (
        <p className="copy-archive-path-error" role="status">
          {error}
        </p>
      ) : null}
    </div>
  );
}

function PagePurposeCard({ section }) {
  if (!section) return null;
  return (
    <aside className="page-purpose-card" aria-label={`${section.title} page purpose`}>
      <p className="eyebrow">What this page is for</p>
      <h3 className="page-purpose-title">{section.title}</h3>
      <p className="page-purpose-statement">{section.purpose}</p>
      <dl className="page-purpose-grid">
        <div>
          <dt>Reads</dt>
          <dd>{section.reads}</dd>
        </div>
        <div>
          <dt>Produces</dt>
          <dd>{section.produces}</dd>
        </div>
      </dl>
    </aside>
  );
}

function MarkdownPreview({ outputPath }) {
  const [state, setState] = useState({ status: "loading", body: "", error: "" });

  useEffect(() => {
    if (!outputPath) {
      setState({ status: "idle", body: "", error: "" });
      return;
    }
    let cancelled = false;
    setState({ status: "loading", body: "", error: "" });
    const url = `/api/library/preview?output_path=${encodeURIComponent(outputPath)}`;
    fetch(url)
      .then((response) => {
        if (cancelled) return null;
        if (!response.ok) {
          return response.json().then(
            (payload) => {
              throw new Error(payload.error || `HTTP ${response.status}`);
            },
            () => {
              throw new Error(`HTTP ${response.status}`);
            },
          );
        }
        return response.text();
      })
      .then((text) => {
        if (cancelled || text === null) return;
        setState({ status: "ready", body: text, error: "" });
      })
      .catch((err) => {
        if (cancelled) return;
        setState({ status: "error", body: "", error: err.message || "Preview failed" });
      });
    return () => {
      cancelled = true;
    };
  }, [outputPath]);

  if (!outputPath) return null;
  if (state.status === "loading") {
    return <p className="markdown-preview-status">Loading preview…</p>;
  }
  if (state.status === "error") {
    return (
      <p className="markdown-preview-status markdown-preview-error" role="status">
        Could not read preview: {state.error}
      </p>
    );
  }
  return (
    <details className="markdown-preview" open>
      <summary>Markdown preview</summary>
      <pre>{state.body}</pre>
    </details>
  );
}

function PollErrorBanner({ error, onDismiss }) {
  if (!error) return null;
  // Show only the message text — never raw stack traces or sensitive context.
  const message = (error && error.message) || "Polling failed";
  return (
    <div className="poll-error-banner" role="status">
      <p className="eyebrow">Auto-refresh failed</p>
      <p className="poll-error-message">{message}</p>
      <button type="button" onClick={onDismiss} aria-label="Dismiss polling error">
        Dismiss
      </button>
    </div>
  );
}

function useWorkspaceNavigation() {
  const [navigation, setNavigation] = useState([]);
  const [pagePurposes, setPagePurposes] = useState([]);
  const [activeSection, setActiveSection] = useState(window.location.hash.replace("#", "") || "dashboard");

  useEffect(() => {
    requestJson("/api/navigation").then((payload) => {
      startTransition(() => setNavigation(payload));
    });
    requestJson("/api/page-purposes").then((payload) => {
      startTransition(() => setPagePurposes(payload));
    });
  }, []);

  useEffect(() => {
    if (!navigation.some((item) => item.id === activeSection)) {
      setActiveSection(navigation[0]?.id || "dashboard");
    }
  }, [navigation, activeSection]);

  useEffect(() => {
    window.location.hash = activeSection;
  }, [activeSection]);

  return { navigation, pagePurposes, activeSection, setActiveSection };
}

function DashboardSection({ section, autoRefreshEnabled }) {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    requestJson("/api/dashboard").then((payload) => {
      startTransition(() => setOverview(payload));
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
      startTransition(() => setOverview(payload));
    },
  });

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

function LibrarySection({
  section,
  autoRefreshEnabled,
  form,
  setForm,
  page,
  setPage,
  pageSize,
  setPageSize,
}) {
  // The form (keyword / sources / since / until), page, and pageSize are
  // owned by App so they survive a section switch. Everything else —
  // fetched data, loading state, selection — stays local to this section
  // and is reset to defaults on remount.
  const [items, setItems] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [emptyState, setEmptyState] = useState(null);
  const [searchNotes, setSearchNotes] = useState({ scope: "", filter: "", result_source: "" });

  const sourceSummary = useMemo(() => form.sources.join(", "), [form.sources]);

  async function runSearch(event, newPage = 1) {
    event?.preventDefault();
    setLoading(true);
    const params = new URLSearchParams();
    if (form.keyword) params.set("keyword", form.keyword);
    if (form.since) params.set("since", form.since);
    if (form.until) params.set("until", form.until);
    form.sources.forEach((source) => params.append("source", source));
    params.set("page", String(newPage));
    params.set("page_size", String(pageSize));
    const payload = await requestJson(`/api/library?${params.toString()}`);
    startTransition(() => {
      setItems(payload.items || []);
      setTotalCount(payload.total_count || 0);
      setTotalPages(payload.total_pages || 1);
      setPage(payload.page || newPage);
      setDetail(payload.items?.[0] || null);
      setEmptyState(payload.empty_state || null);
      setSearchNotes(payload.search_notes || { scope: "", filter: "", result_source: "" });
      setLoading(false);
    });
  }

  // Initial mount: trigger one search so the user has results. We rely on
  // the lifted form state for keyword/sources/page so the result page
  // already reflects whatever the user previously typed in App — we do
  // NOT force `newPage = 1` here, we use the current `page` prop.
  const hasMountedRef = useRef(false);
  useEffect(() => {
    if (hasMountedRef.current) return;
    hasMountedRef.current = true;
    runSearch(null, page);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Auto-refresh: re-fetch the current page with the same form, preserving
  // keyword / sources / page so the user's in-progress work is not lost.
  // We intentionally do NOT touch `form`, `page`, or `loading` here.
  const { lastError: libraryLastError, dismissError: libraryDismissError } = useAutoRefresh({
    section: "library",
    enabled: Boolean(autoRefreshEnabled),
    fetcher: () => {
      const params = new URLSearchParams();
      if (form.keyword) params.set("keyword", form.keyword);
      if (form.since) params.set("since", form.since);
      if (form.until) params.set("until", form.until);
      form.sources.forEach((source) => params.append("source", source));
      params.set("page", String(page));
      params.set("page_size", String(pageSize));
      return requestJson(`/api/library?${params.toString()}`);
    },
    onData: (_section, payload) => {
      startTransition(() => {
        setItems(payload.items || []);
        setTotalCount(payload.total_count || 0);
        setTotalPages(payload.total_pages || 1);
        if (payload.items?.[0]) setDetail(payload.items[0]);
        setEmptyState(payload.empty_state || null);
        setSearchNotes(payload.search_notes || { scope: "", filter: "", result_source: "" });
      });
    },
  });

  function handlePageSizeChange(event) {
    const newSize = parseInt(event.target.value, 10);
    setPageSize(newSize);
    setPage(1);
    runSearch(null, 1);
  }

  function goToPage(newPage) {
    if (newPage < 1 || newPage > totalPages) return;
    runSearch(null, newPage);
  }

  async function selectItem(outputPath) {
    const payload = await requestJson(`/api/library/item?output_path=${encodeURIComponent(outputPath)}`);
    startTransition(() => setDetail(payload));
  }

  function toggleSource(source) {
    setForm((current) => {
      const nextSources = current.sources.includes(source)
        ? current.sources.filter((item) => item !== source)
        : [...current.sources, source];
      return { ...current, sources: nextSources };
    });
  }

  const currentStart = (page - 1) * pageSize + 1;
  const currentEnd = Math.min(page * pageSize, totalCount);

  return (
    <section className="library-workspace">
      <PollErrorBanner error={libraryLastError} onDismiss={libraryDismissError} />
      <header className="library-filter-bar">
        <details className="library-meta-collapsible">
          <summary className="eyebrow">About this page</summary>
          <PagePurposeCard section={section} />
        </details>
        <details className="library-meta-collapsible">
          <summary className="eyebrow">Search scope</summary>
          <p className="library-scope-snapshot">{searchNotes.scope}</p>
          <p className="supporting">{searchNotes.filter}</p>
        </details>
        <form className="library-filter-form" onSubmit={runSearch}>
          <label className="library-filter-keyword" aria-label="Search keyword">
            <span className="field-label">keyword</span>
            <input
              value={form.keyword}
              onChange={(event) => setForm((current) => ({ ...current, keyword: event.target.value }))}
              placeholder="e.g. agent harness, claude code, arxiv"
            />
          </label>
          <div className="library-filter-sources">
            <span className="field-label">sources</span>
            <div className="source-list">
              {SOURCE_OPTIONS.map((source) => (
                <label key={source} className={`source-toggle ${form.sources.includes(source) ? "active" : ""}`}>
                  <input type="checkbox" checked={form.sources.includes(source)} onChange={() => toggleSource(source)} />
                  <span>{source}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="library-filter-dates">
            <label>
              <span className="field-label">since</span>
              <input value={form.since} onChange={(event) => setForm((current) => ({ ...current, since: event.target.value }))} placeholder="2026-05-01" />
            </label>
            <label>
              <span className="field-label">until</span>
              <input value={form.until} onChange={(event) => setForm((current) => ({ ...current, until: event.target.value }))} placeholder="2026-05-31" />
            </label>
          </div>
          <button type="submit" className="library-filter-search">Search</button>
          {form.keyword || form.since || form.until || form.sources.length ? (
            <button
              type="button"
              className="library-filter-clear"
              onClick={() => {
                setForm({ keyword: "", sources: [], since: "", until: "" });
                setPage(1);
              }}
            >
              Clear filters
            </button>
          ) : null}
          <p className="library-filter-count">
            {totalCount === 0 ? (
              "No results match your filters."
            ) : (
              <>Showing {currentStart}–{currentEnd} of {totalCount} · sources: {sourceSummary || "none"}</>
            )}
          </p>
        </form>
      </header>

      <div className="library-workspace-grid">
        <div className="panel result-panel">
          <div className="result-panel-header">
            <p className="eyebrow">Results</p>
            <p className="supporting">{searchNotes.result_source}</p>
          </div>
          {loading ? (
            <div className="loading-indicator" role="status" aria-live="polite">
              <span className="spinner" aria-hidden="true" />
              <span>Loading…</span>
            </div>
          ) : null}

          {!loading && items.length === 0 && emptyState ? (
            <div className="empty-state-panel" role="status">
              <p className="eyebrow">Empty results</p>
              <p className="empty-state-explanation">{emptyState.explanation}</p>
              <ul className="plain-list">
                {emptyState.next_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ul>
            </div>
          ) : null}

          <ul className="result-list">
            {items.map((item) => (
              <li key={`${item.output_path}-${item.title}`}>
                <button type="button" className={`result-card ${detail?.output_path === item.output_path ? "active" : ""}`} onClick={() => selectItem(item.output_path)}>
                  <span className="result-meta">{item.source} · {item.item_type || "unknown"}</span>
                  <strong>{item.title}</strong>
                  <p>{item.summary || "No summary"}</p>
                  <span className="result-meta">{item.published_at || item.updated_at || ""}{item.tags?.length ? ` · ${item.tags.slice(0, 3).join(", ")}` : ""}</span>
                </button>
              </li>
            ))}
          </ul>

          {totalPages > 1 ? (
            <div className="pagination-controls">
              <button type="button" onClick={() => goToPage(page - 1)} disabled={page <= 1}>‹ Previous</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                let pageNum = i + 1;
                if (totalPages > 5) {
                  if (page > 3) pageNum = page - 2 + i;
                  if (page > totalPages - 2) pageNum = totalPages - 4 + i;
                }
                return (
                  <button key={pageNum} type="button" className={page === pageNum ? "active" : ""} onClick={() => goToPage(pageNum)}>
                    {pageNum}
                  </button>
                );
              })}
              <button type="button" onClick={() => goToPage(page + 1)} disabled={page >= totalPages}>Next ›</button>
            </div>
          ) : null}

          <div className="pagination-info">
            <span>page size</span>
            <select value={pageSize} onChange={handlePageSizeChange}>
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
            </select>
          </div>
        </div>

        <div className="panel detail-panel">
          <p className="eyebrow">Item detail</p>
        {detail ? (
          <>
            <h2>{detail.title}</h2>
            <p>{detail.summary || "No summary"}</p>
            <dl className="detail-grid">
              <div>
                <dt>Source</dt>
                <dd>{detail.source}</dd>
              </div>
              <div>
                <dt>Type</dt>
                <dd>{detail.item_type || "unknown"}</dd>
              </div>
              <div>
                <dt>Authors</dt>
                <dd>{detail.authors?.join(", ") || "n/a"}</dd>
              </div>
              <div>
                <dt>Published</dt>
                <dd>{detail.published_at || detail.updated_at || "n/a"}</dd>
              </div>
              <div>
                <dt>Tags</dt>
                <dd>{detail.tags?.join(", ") || "n/a"}</dd>
              </div>
              <div>
                <dt>Archive path</dt>
                <dd>{detail.output_path}</dd>
              </div>
            </dl>
            <MarkdownPreview outputPath={detail.output_path} />
            <div className="detail-actions">
              <a href="#markdown-preview">Preview Markdown</a>
              <a href={detail.canonical_url} target="_blank" rel="noreferrer">Open source link</a>
              <CopyArchivePathButton outputPath={detail.output_path} />
              <span className="detail-actions-spacer" aria-hidden="true" />
              <span className="library-about-local-files">
                About local files: paste the copied path into your OS file manager (Finder / Explorer) — this workspace deliberately does not open local files itself.
              </span>
            </div>
          </>
        ) : (
          <p>Select a result to inspect the local metadata.</p>
        )}
      </div>
      </div>
    </section>
  );
}

function BriefingSection({ section, autoRefreshEnabled }) {
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
    const payload = await requestJson(path, {
      method: "POST",
      body: JSON.stringify(form),
    });
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
            <ul className="plain-list">
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

function CollectSection({ section, autoRefreshEnabled }) {
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
        setErrorMessage("");
      });
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

        {!result ? (
          <details className="collect-first-run-hint">
            <summary>Tips for first-time users</summary>
            <p className="empty-state-explanation">
              Pick a source above, fill the inputs, then press <strong>Run now</strong>. Collected items land in
              <code>output/&lt;source&gt;/</code> and become searchable from the Library.
            </p>
            <ul className="plain-list compact-list">
              <li>GitHub — one repo or a search keyword.</li>
              <li>arXiv Papers — one or more categories.</li>
              <li>WeChat — a single public-account article URL.</li>
            </ul>
          </details>
        ) : null}
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
          <ul className="plain-list compact-list">
            <li>Queued / running / failed job history timeline</li>
            <li>Scheduled collection and refresh policy controls</li>
            <li>Dashboard freshness badges fed by the jobs layer</li>
          </ul>
        </div>
      </div>
    </section>
  );
}

export default function App() {
  const { navigation, pagePurposes, activeSection, setActiveSection } = useWorkspaceNavigation();
  // Auto-refresh is on by default; the user can toggle it off in the topbar.
  // Each section re-fetches its data endpoint at 5s intervals while on.
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(true);

  // ── Lifted Library form state ──────────────────────────────────────────
  // The Library page's form (keyword / sources / since / until / page /
  // pageSize) is owned by App, NOT by LibrarySection. If it lived in
  // LibrarySection then switching tabs would unmount the component and
  // reset the form to its default — losing the user's in-progress work.
  // Lifting the state here keeps the form alive across section switches.
  const [libraryForm, setLibraryForm] = useState({
    keyword: "agent",
    sources: ["github", "papers", "wechat"],
    since: "",
    until: "",
  });
  const [libraryPage, setLibraryPage] = useState(1);
  const [libraryPageSize, setLibraryPageSize] = useState(20);

  const currentPurpose = pagePurposes.find((p) => p.id === activeSection) || null;

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Intel Station</p>
          <h1>Local research workspace</h1>
        </div>
        <label className="auto-refresh-toggle" title="Auto-refresh the active section every 5 seconds">
          <input
            type="checkbox"
            checked={autoRefreshEnabled}
            onChange={(event) => setAutoRefreshEnabled(event.target.checked)}
          />
          <span>Auto-refresh (5s)</span>
        </label>
        <p className="tagline">Editorial interface for archive coverage, local search, and briefing generation.</p>
      </header>

      <nav className="tabbar">
        {navigation.map((item) => (
          <button
            key={item.id}
            type="button"
            className={item.id === activeSection ? "active" : ""}
            onClick={() => startTransition(() => setActiveSection(item.id))}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main>
        {activeSection === "dashboard" ? (
          <DashboardSection section={currentPurpose} autoRefreshEnabled={autoRefreshEnabled} />
        ) : null}
        {activeSection === "library" ? (
          <LibrarySection
            section={currentPurpose}
            autoRefreshEnabled={autoRefreshEnabled}
            form={libraryForm}
            setForm={setLibraryForm}
            page={libraryPage}
            setPage={setLibraryPage}
            pageSize={libraryPageSize}
            setPageSize={setLibraryPageSize}
          />
        ) : null}
        {activeSection === "briefing" ? (
          <BriefingSection section={currentPurpose} autoRefreshEnabled={autoRefreshEnabled} />
        ) : null}
        {activeSection === "collect" ? (
          <CollectSection section={currentPurpose} autoRefreshEnabled={autoRefreshEnabled} />
        ) : null}
      </main>
    </div>
  );
}