import { useEffect, useState } from "react";

export function CopyArchivePathButton({ outputPath }) {
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

export function PagePurposeCard({ section }) {
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

export function MarkdownPreview({ outputPath }) {
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

export function PollErrorBanner({ error, onDismiss }) {
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
