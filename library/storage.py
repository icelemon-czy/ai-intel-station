from __future__ import annotations

import json
import logging
from pathlib import Path

from .items import ResearchItem


_log = logging.getLogger(__name__)


def iter_research_item_sidecars(output_root: Path) -> list[Path]:
    output_root = Path(output_root)
    sidecars = []
    for pattern in ("**/research-item.json", "**/*.research-item.json", "**/research-items.jsonl"):
        sidecars.extend(output_root.glob(pattern))
    return sorted(path for path in sidecars if path.is_file())


def load_research_items(output_root: Path) -> list[ResearchItem]:
    """Read every ResearchItem sidecar under ``output_root``.

    A corrupted sidecar (truncated write, manual edit gone wrong,
    schema change with stale data on disk) used to raise JSONDecodeError
    and refuse to load the rest of the archive. Operators would then
    think their whole library was broken instead of one entry.

    Now: a single corrupt sidecar logs a warning, skips itself, and
    the rest of the archive loads. A corrupt line inside an otherwise
    good JSONL file likewise skips the line without aborting.
    """
    items = []
    for sidecar_path in iter_research_item_sidecars(output_root):
        try:
            if sidecar_path.name == "research-items.jsonl":
                text = sidecar_path.read_text(encoding="utf-8")
                for lineno, raw in enumerate(text.splitlines(), start=1):
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    try:
                        items.append(ResearchItem(**json.loads(stripped)))
                    except json.JSONDecodeError as exc:
                        _log.warning(
                            "skipping corrupt JSONL line %d in %s: %s",
                            lineno,
                            sidecar_path,
                            exc,
                        )
            else:
                items.append(
                    ResearchItem(**json.loads(sidecar_path.read_text(encoding="utf-8")))
                )
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            _log.warning("skipping corrupt sidecar %s: %s", sidecar_path, exc)

    return items
