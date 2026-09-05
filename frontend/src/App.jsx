import { startTransition, useEffect, useState } from "react";
import { requestJson } from "./api.js";
import { BriefingSection } from "./BriefingSection.jsx";
import { CollectSection } from "./CollectSection.jsx";
import { DashboardSection } from "./DashboardSection.jsx";
import { LibrarySection } from "./LibrarySection.jsx";

function useWorkspaceNavigation() {
  const [navigation, setNavigation] = useState([]);
  const [pagePurposes, setPagePurposes] = useState([]);
  const [activeSection, setActiveSection] = useState(window.location.hash.replace("#", "") || "dashboard");

  useEffect(() => {
    requestJson("/api/navigation").then((payload) => {
      startTransition(() => setNavigation(payload));
    }).catch((err) => {
      // Without this catch a 5xx leaves `navigation = []` and the
      // navigation bar never renders — making the workspace unusable.
      // Surface the failure to the console at minimum so the symptom is
      // diagnosable; the visible fallback is the "dashboard" section
      // the existing effect already lands on.
      console.error("failed to load /api/navigation:", err);
    });
    requestJson("/api/page-purposes").then((payload) => {
      startTransition(() => setPagePurposes(payload));
    }).catch((err) => {
      console.error("failed to load /api/page-purposes:", err);
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
          <CollectSection
            section={currentPurpose}
            autoRefreshEnabled={autoRefreshEnabled}
            setActiveSection={setActiveSection}
          />
        ) : null}
      </main>
    </div>
  );
}
