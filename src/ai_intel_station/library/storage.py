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


def _item_from_dict(payload: dict) -> ResearchItem | None:
    """Build a ResearchItem from a JSON sidecar dict, dropping keys
    that the current dataclass does not understand.

    Older runs of ``research backfill`` (or fixtures) may carry extra
    fields — ``ranking_score``, ``note_from_a_friend``, etc. — that a
    strict dataclass constructor would reject with TypeError. We
    filter to the fields actually declared on the class so a stale
    sidecar does not refuse to load.

    A non-mapping payload (a hand-edited JSON file with a list or
    scalar at the top level) is also rejected — without the
    isinstance check, ``payload.items()`` would raise AttributeError
    mid-load.
    """
    if not isinstance(payload, dict):
        return None
    from dataclasses import fields

    valid_keys = {f.name for f in fields(ResearchItem)}
    return ResearchItem(**{k: v for k, v in payload.items() if k in valid_keys})


def load_research_items(output_root: Path) -> list[ResearchItem]:
    """Read every ResearchItem sidecar under ``output_root``.

    A corrupted sidecar (truncated write, manual edit gone wrong,
    schema change with stale data on disk) used to raise JSONDecodeError
    and refuse to load the rest of the archive. Operators would then
    think their whole library was broken instead of one entry.

    Now: a single corrupt sidecar logs a warning, skips itself, and
    the rest of the archive loads. A corrupt line inside an otherwise
    good JSONL file likewise skips the line without aborting.
    Extra keys not understood by the current ResearchItem are silently
    dropped so older sidecars from a previous schema don't break
    loading.
    """
    items = []
    for sidecar_path in iter_research_item_sidecars(output_root):
        try:
            if sidecar_path.name == "research-items.jsonl":
                # JSONL files use a single read_text for the whole
                # document, so the BOM at the start of the first
                # line must be stripped once at the document level
                # rather than per-line.
                try:
                    text = sidecar_path.read_text(encoding="utf-8-sig")
                except UnicodeDecodeError as exc:
                    _log.warning("skipping corrupt sidecar %s: %s", sidecar_path, exc)
                    continue
                for lineno, raw in enumerate(text.splitlines(), start=1):
                    stripped = raw.strip()
                    if not stripped:
                        continue
                    try:
                        item = _item_from_dict(json.loads(stripped))
                    except json.JSONDecodeError as exc:
                        _log.warning(
                            "skipping corrupt JSONL line %d in %s: %s",
                            lineno,
                            sidecar_path,
                            exc,
                        )
                        continue
                    if item is not None:
                        items.append(item)
            else:
                item = _item_from_dict(
                    json.loads(sidecar_path.read_text(encoding="utf-8"))
                )
                if item is not None:
                    items.append(item)
        except (json.JSONDecodeError, OSError, ValueError, UnicodeDecodeError) as exc:
            # If the sidecar looks like a UTF-8 BOM, retry with
            # utf-8-sig which transparently strips the leading BOM.
            # Operators who paste a sidecar from a Windows editor
            # frequently get a leading BOM; without this retry the
            # file is logged as corrupt and skipped. The retry can
            # raise either UnicodeDecodeError (older Python) or
            # JSONDecodeError (newer Python, where json.loads sees the
            # ﻿ BOM and raises a confusing error message).
            is_bom_error = (
                isinstance(exc, (UnicodeDecodeError, json.JSONDecodeError))
                and "BOM" in getattr(exc, "msg", "")
            )
            if is_bom_error:
                try:
                    payload = json.loads(
                        sidecar_path.read_text(encoding="utf-8-sig")
                    )
                    item = _item_from_dict(payload)
                    if item is not None:
                        items.append(item)
                    _log.warning(
                        "sidecar %s had a UTF-8 BOM; loaded with utf-8-sig",
                        sidecar_path,
                    )
                    continue
                except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc2:
                    _log.warning(
                        "skipping corrupt sidecar %s: %s", sidecar_path, exc2
                    )
                    continue
            _log.warning("skipping corrupt sidecar %s: %s", sidecar_path, exc)

    return items
