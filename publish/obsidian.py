from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "briefing"


def briefing_output_path(output_root: Path, section: str, title: str) -> Path:
    return Path(output_root) / "briefing" / section / f"{slugify(title)}.md"


def write_markdown(path: Path, content: str) -> Path:
    """Atomically write Markdown content to ``path``.

    Writes to a sibling temp file, fsyncs, then ``os.replace``s into place.
    Without this, an interrupted ``path.write_text()`` either leaves the
    previous file untouched (safe but stale) or \u2014 in the middle of an
    ``open(...).write()`` followed by SIGTERM \u2014 produces a half-written
    ``path`` that downstream readers parse as corrupted Markdown
    (truncated frontmatter etc.).

    Returns ``path`` for chaining.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content.rstrip() + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        # Best-effort cleanup \u2014 the temp file is in the same directory so
        # it cannot outlive a directory delete.
        try:
            os.unlink(tmp_path)
        except FileNotFoundError:
            pass
        raise
    return path
