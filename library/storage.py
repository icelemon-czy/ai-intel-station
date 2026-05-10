from __future__ import annotations

import json
from pathlib import Path

from .items import ResearchItem


def iter_research_item_sidecars(output_root: Path) -> list[Path]:
    output_root = Path(output_root)
    sidecars = []
    for pattern in ("**/research-item.json", "**/*.research-item.json", "**/research-items.jsonl"):
        sidecars.extend(output_root.glob(pattern))
    return sorted(path for path in sidecars if path.is_file())


def load_research_items(output_root: Path) -> list[ResearchItem]:
    items = []
    for sidecar_path in iter_research_item_sidecars(output_root):
        if sidecar_path.name == "research-items.jsonl":
            for line in sidecar_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                items.append(ResearchItem(**json.loads(stripped)))
        else:
            items.append(ResearchItem(**json.loads(sidecar_path.read_text(encoding="utf-8"))))

    return items
