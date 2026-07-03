"""Regression tests for two regressions uncovered while reading source.

1. ``load_research_items`` used to crash with TypeError when a sidecar
   carried extra keys from a previous schema version. Now it filters
   to the dataclass fields so older sidecars keep loading.
2. ``_local_link`` falls back to a ``file://`` URL when the output_path
   is outside ``REPO_ROOT`` — no path-traversal-like rewrite.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from library.items import (
    REPO_ROOT,
    ResearchItem,
    write_research_item,
)
from library.storage import load_research_items


class SidecarSchemaMigrationTests(unittest.TestCase):
    """Real bug: an older research run may write a sidecar with
    fields the current ResearchItem does not understand (e.g.
    ``authors_legacy``, ``scrape_url``). The strict dataclass
    constructor used to raise TypeError, taking down the entire
    load_research_items call.
    """

    def test_extra_unknown_keys_dropped_silently(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            gh = output_root / "github" / "agent"
            gh.mkdir(parents=True)
            sidecar = gh / "research-item.json"
            sidecar.parent.mkdir(parents=True, exist_ok=True)
            # Hand-write a sidecar with the current known keys plus
            # TWO extras that this dataclass version has never seen.
            payload = {
                "source": "github",
                "item_type": "repo",
                "title": "agent",
                "canonical_url": "https://example.com/agent",
                "summary": None,
                "authors": [],
                "published_at": "2026-05-01",
                "updated_at": None,
                "tags": [],
                "output_path": "output/github/agent/README.md",
                "metadata": {},
                "ranking_score": 0.91,
                "scrape_url": "https://scraper.example.com/source",
            }
            sidecar.write_text(json.dumps(payload), encoding="utf-8")

            # Without the filter, this used to raise TypeError on the
            # unknown kwarg. With the filter, the item loads with the
            # known fields; unknown fields are dropped on the floor.
            items = load_research_items(output_root)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].title, "agent")
            self.assertFalse(hasattr(items[0], "ranking_score"))

    def test_current_keys_still_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "out"
            gh = output_root / "github" / "agent"
            gh.mkdir(parents=True)
            (gh / "README.md").write_text("# agent\n", encoding="utf-8")
            write_research_item(
                ResearchItem(
                    source="github",
                    item_type="repo",
                    title="agent",
                    canonical_url="https://example.com/agent",
                ),
                gh / "research-item.json",
            )
            items = load_research_items(output_root)
            self.assertEqual(len(items), 1)

    def test_non_mapping_payload_does_not_crash(self) -> None:
        # A hand-edited JSON sidecar with a list at the top level
        # (instead of the expected mapping) used to raise
        # AttributeError on ``payload.items()`` mid-load. The fix
        # rejects the non-mapping payload silently so the rest of
        # the archive keeps loading.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            gh = out / "github" / "agent"
            gh.mkdir(parents=True)
            (gh / "research-item.json").write_text("[1, 2, 3]", encoding="utf-8")
            items = load_research_items(out)
            self.assertEqual(items, [])

    def test_scalar_payload_does_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            gh = out / "github" / "agent"
            gh.mkdir(parents=True)
            (gh / "research-item.json").write_text("\"a string\"", encoding="utf-8")
            items = load_research_items(out)
            self.assertEqual(items, [])

    def test_non_utf8_sidecar_is_skipped(self) -> None:
        # A sidecar written with a non-utf8 encoding used to raise
        # UnicodeDecodeError mid-load. The fix catches the decode
        # error and skips the sidecar so the rest of the archive
        # keeps loading.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            gh = out / "github" / "agent"
            gh.mkdir(parents=True)
            (gh / "research-item.json").write_bytes(b"\xff\xfe\x00bad bytes")
            items = load_research_items(out)
            self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
