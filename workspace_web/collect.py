from __future__ import annotations

from pathlib import Path

from collect.service import run_collection


DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "output"

COLLECT_SOURCE_FORMS: dict[str, dict[str, object]] = {
    "github": {
        "id": "github",
        "label": "GitHub",
        "description": "Collect from GitHub repositories",
        "purpose": "Snapshot a single repository or pull a batch of repos from a search query.",
        "required_input": "owner/repo (single repo) OR search keyword with search mode enabled",
        "output_dir": "output/github/",
        "dependency_hint": "Requires the GitHub CLI (`gh`) to be installed and authenticated.",
        "fields": [
            {"name": "query", "label": "Search Query", "type": "text", "placeholder": "owner/repo or search keywords"},
            {"name": "search", "label": "Search Mode", "type": "boolean", "description": "Enable search mode instead of single repo"},
            {"name": "max", "label": "Max Results", "type": "number", "default": 10},
        ],
    },
    "papers": {
        "id": "papers",
        "label": "arXiv Papers",
        "description": "Collect from arXiv papers",
        "purpose": "Pull paper abstracts and metadata for one or more arXiv categories.",
        "required_input": "arXiv category code (e.g. cs.AI) and maximum number of results",
        "output_dir": "output/papers/",
        "dependency_hint": "Uses the arXiv public API; no API key or authentication required.",
        "fields": [
            {"name": "category", "label": "Category", "type": "text", "placeholder": "cs.AI, cs.LG, cs.CL..."},
            {"name": "max", "label": "Max Results", "type": "number", "default": 10},
        ],
    },
    "wechat": {
        "id": "wechat",
        "label": "WeChat Articles",
        "description": "Collect WeChat public account articles",
        "purpose": "Fetch a single WeChat public account article as local Markdown.",
        "required_input": "WeChat article URL (mp.weixin.qq.com)",
        "output_dir": "output/wechat/",
        "dependency_hint": "Uses the Camoufox anti-detection browser runtime; first run may be slow.",
        "fields": [
            {"name": "url", "label": "Article URL", "type": "text", "placeholder": "https://mp.weixin.qq.com/s/..."},
        ],
    },
}


def list_collect_sources() -> list[dict[str, object]]:
    return list(COLLECT_SOURCE_FORMS.values())


def get_collect_form(source: str) -> dict[str, object]:
    if source not in COLLECT_SOURCE_FORMS:
        return {"id": source, "label": source, "description": "Unknown source", "fields": []}
    return dict(COLLECT_SOURCE_FORMS[source])


def run_collect(
    source: str,
    fields: dict[str, object],
    output_root: Path | None = None,
) -> dict[str, object]:
    root = Path(output_root) if output_root is not None else DEFAULT_OUTPUT_ROOT
    return run_collection(source, fields, root).to_payload()
