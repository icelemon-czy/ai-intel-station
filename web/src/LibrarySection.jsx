import { startTransition, useEffect, useMemo, useRef, useState } from "react";
import { useAutoRefresh } from "./autoRefresh.react.js";
import { requestJson } from "./api.js";
import { SOURCE_OPTIONS } from "./workspaceOptions.js";
import { CopyArchivePathButton, MarkdownPreview, PagePurposeCard, PollErrorBanner } from "./workspaceShared.jsx";

export function LibrarySection({
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
    let payload;
    try {
      payload = await requestJson(`/api/library?${params.toString()}`);
    } catch (err) {
      // Without this catch the loading spinner stays spinning forever
      // after a 5xx — search appears to have silently hung.
      startTransition(() => {
        setLoading(false);
        setEmptyState({
          explanation: `Search failed: ${err.message || err}`,
          next_steps: ["Try a different keyword", "Check the server logs"],
        });
      });
      return;
    }
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
    let payload;
    try {
      payload = await requestJson(`/api/library/item?output_path=${encodeURIComponent(outputPath)}`);
    } catch (err) {
      // Surface the fetch failure into the detail panel so the user can
      // see why their click did nothing — a silent console error here
      // makes the workspace look broken.
      startTransition(() => setDetail({ error: err.message || String(err) }));
      return;
    }
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
              <ul className="plainList">
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
        {detail && detail.error ? (
          <div className="status-banner error" role="status">
            <strong>Could not load item:</strong> {detail.error}
          </div>
        ) : detail ? (
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
