import { startTransition, useEffect, useMemo, useState } from "react";

const SOURCE_OPTIONS = ["github", "papers", "wechat"];

async function requestJson(path, options) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json();
}

function useWorkspaceNavigation() {
  const [navigation, setNavigation] = useState([]);
  const [activeSection, setActiveSection] = useState(window.location.hash.replace("#", "") || "dashboard");

  useEffect(() => {
    requestJson("/api/navigation").then((payload) => {
      startTransition(() => {
        setNavigation(payload);
        if (!payload.some((item) => item.id === activeSection)) {
          setActiveSection(payload[0]?.id || "dashboard");
        }
      });
    });
  }, [activeSection]);

  useEffect(() => {
    window.location.hash = activeSection;
  }, [activeSection]);

  return { navigation, activeSection, setActiveSection };
}

function DashboardSection() {
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    requestJson("/api/dashboard").then((payload) => {
      startTransition(() => setOverview(payload));
    });
  }, []);

  if (!overview) {
    return <section className="panel shimmer">Loading dashboard…</section>;
  }

  return (
    <section className="panel dashboard-grid">
      <div className="hero-card">
        <p className="eyebrow">Local archive</p>
        <h2>{overview.total_items} research items</h2>
        <p>Dashboard, Library, and Briefing all read from the same local sidecar truth.</p>
      </div>

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

      <div className="metric-card">
        <p className="eyebrow">Coverage gaps</p>
        {overview.missing_sources.length ? (
          <ul className="plain-list">
            {overview.missing_sources.map((source) => (
              <li key={source}>{source}</li>
            ))}
          </ul>
        ) : (
          <p>No missing sources in the current local archive.</p>
        )}
      </div>

      <div className="metric-card wide">
        <p className="eyebrow">Recent briefings</p>
        {overview.recent_briefings.length ? (
          <ul className="plain-list">
            {overview.recent_briefings.map((entry) => (
              <li key={entry.path}>
                <strong>{entry.title}</strong>
                <span>{entry.path}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p>No briefing artifacts yet.</p>
        )}
      </div>

      <div className="metric-card wide">
        <p className="eyebrow">Orphan markdown</p>
        {overview.orphan_markdown_paths.length ? (
          <ul className="plain-list compact">
            {overview.orphan_markdown_paths.map((path) => (
              <li key={path}>{path}</li>
            ))}
          </ul>
        ) : (
          <p>No orphan markdown files detected.</p>
        )}
      </div>
    </section>
  );
}

function LibrarySection() {
  const [form, setForm] = useState({ keyword: "agent", sources: ["github", "papers", "wechat"], since: "", until: "" });
  const [items, setItems] = useState([]);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);

  const sourceSummary = useMemo(() => form.sources.join(", "), [form.sources]);

  async function runSearch(event) {
    event?.preventDefault();
    setLoading(true);
    const params = new URLSearchParams();
    if (form.keyword) params.set("keyword", form.keyword);
    if (form.since) params.set("since", form.since);
    if (form.until) params.set("until", form.until);
    form.sources.forEach((source) => params.append("source", source));
    const payload = await requestJson(`/api/library?${params.toString()}`);
    startTransition(() => {
      setItems(payload);
      setDetail(payload[0] || null);
      setLoading(false);
    });
  }

  useEffect(() => {
    runSearch();
  }, []);

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

  return (
    <section className="library-layout">
      <form className="panel search-panel" onSubmit={runSearch}>
        <p className="eyebrow">Local library</p>
        <label>
          Keyword
          <input value={form.keyword} onChange={(event) => setForm((current) => ({ ...current, keyword: event.target.value }))} />
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

        <div className="date-row">
          <label>
            Since
            <input value={form.since} onChange={(event) => setForm((current) => ({ ...current, since: event.target.value }))} placeholder="2026-05-01" />
          </label>
          <label>
            Until
            <input value={form.until} onChange={(event) => setForm((current) => ({ ...current, until: event.target.value }))} placeholder="2026-05-31" />
          </label>
        </div>

        <button type="submit">Search local archive</button>
        <p className="supporting">Current sources: {sourceSummary || "none"}</p>
      </form>

      <div className="panel result-panel">
        <p className="eyebrow">Results</p>
        {loading ? <p>Refreshing results…</p> : null}
        <ul className="result-list">
          {items.map((item) => (
            <li key={`${item.output_path}-${item.title}`}>
              <button type="button" className="result-card" onClick={() => selectItem(item.output_path)}>
                <span className="result-meta">{item.source}</span>
                <strong>{item.title}</strong>
                <p>{item.summary || "No summary"}</p>
              </button>
            </li>
          ))}
        </ul>
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
                <dt>Authors</dt>
                <dd>{detail.authors?.join(", ") || "n/a"}</dd>
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
            <a href={detail.canonical_url} target="_blank" rel="noreferrer">Open source link</a>
          </>
        ) : (
          <p>Select a result to inspect the local metadata.</p>
        )}
      </div>
    </section>
  );
}

function BriefingSection() {
  const [form, setForm] = useState({ mode: "digest", keyword: "agent", title: "AI Agents", sources: ["github", "papers", "wechat"], since: "", until: "" });
  const [preview, setPreview] = useState("");
  const [savedPath, setSavedPath] = useState("");
  const [loading, setLoading] = useState(false);

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
      setLoading(false);
    });
  }

  return (
    <section className="briefing-layout">
      <div className="panel control-panel">
        <p className="eyebrow">Briefing workspace</p>
        <label>
          Mode
          <select value={form.mode} onChange={(event) => updateField("mode", event.target.value)}>
            <option value="digest">digest</option>
            <option value="reading-list">reading-list</option>
          </select>
        </label>
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
        {loading ? <p>Working on local briefing…</p> : null}
        {savedPath ? <p className="supporting">Saved: {savedPath}</p> : <p className="supporting">Preview first, then save when the local result looks right.</p>}
      </div>

      <div className="panel preview-panel">
        <p className="eyebrow">Markdown preview</p>
        <pre>{preview || "Run preview to inspect the derived Markdown before saving."}</pre>
      </div>
    </section>
  );
}

export default function App() {
  const { navigation, activeSection, setActiveSection } = useWorkspaceNavigation();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI Intel Station</p>
          <h1>Local research workspace</h1>
        </div>
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
        {activeSection === "dashboard" ? <DashboardSection /> : null}
        {activeSection === "library" ? <LibrarySection /> : null}
        {activeSection === "briefing" ? <BriefingSection /> : null}
      </main>
    </div>
  );
}