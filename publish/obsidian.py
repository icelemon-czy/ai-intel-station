from __future__ import annotations

import re
from pathlib import Path


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "briefing"


def briefing_output_path(output_root: Path, section: str, title: str) -> Path:
    return Path(output_root) / "briefing" / section / f"{slugify(title)}.md"


def write_markdown(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
    return path
