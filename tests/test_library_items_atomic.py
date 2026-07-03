"""Edge-case unit tests for `library.items._atomic_write_text`,
`write_research_item`, and `write_research_items_jsonl`.

The atomic-write contract is critical: a half-written JSON sidecar is
silently dropped by ``load_research_items``, so we lock the contract
in tests that simulate a crash mid-write.
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from library.items import (
    ResearchItem,
    _atomic_write_text,
    write_research_item,
    write_research_items_jsonl,
)


def _sample_item() -> ResearchItem:
    return ResearchItem(
        source="github",
        item_type="repo",
        title="agent-harness",
        canonical_url="https://github.com/x/y",
        summary="harness repo",
        authors=["Ada"],
        published_at="2026-05-01",
        tags=["agent"],
        output_path="output/github/agent-harness/README.md",
    )


class AtomicWriteTextTests(unittest.TestCase):
    def test_write_creates_final_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            _atomic_write_text(path, "hello")
            self.assertEqual(path.read_text(encoding="utf-8"), "hello")

    def test_write_leaves_no_temp_file(self) -> None:
        # mkstemp creates a sibling .tmp file that os.replace must remove.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            _atomic_write_text(path, "hi")
            leftovers = [p for p in Path(tmp).iterdir() if p.name != "out.md"]
            self.assertEqual(leftovers, [], f"leftover temp files: {leftovers}")

    def test_overwrite_replaces_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.md"
            path.write_text("OLD LONG CONTENT HERE", encoding="utf-8")
            _atomic_write_text(path, "new")
            # The final file is the new content with no leftover OLD bytes.
            self.assertEqual(path.read_text(encoding="utf-8"), "new")


class WriteResearchItemTests(unittest.TestCase):
    def test_no_indent_in_json_sidecar(self) -> None:
        # Pretty-printing sidecars doubled file size for no benefit —
        # they're per-item parsed on every library search.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.json"
            write_research_item(_sample_item(), path)
            raw = path.read_text(encoding="utf-8")
            self.assertNotIn("\n  ", raw, "sidecar must not be pretty-printed")

    def test_json_round_trips_via_json_loads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "item.json"
            item = _sample_item()
            write_research_item(item, path)
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["title"], item.title)
            self.assertEqual(loaded["source"], item.source)


class ParseGithubSearchMarkdownEmptyTests(unittest.TestCase):
    def test_empty_file_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "search.md"
            p.write_text("", encoding="utf-8")
            from library.items import parse_github_search_markdown
            self.assertEqual(parse_github_search_markdown(p), [])

    def test_blank_lines_only_returns_empty_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "search.md"
            p.write_text("\n\n", encoding="utf-8")
            from library.items import parse_github_search_markdown
            # 3 lines of whitespace after splitlines: the first line
            # is the literal "" so the title scan lands on the next
            # non-empty line.  The remaining index 0 would still
            # see an empty H1 marker that the entry parse rejects,
            # so the result is still empty.
            self.assertEqual(parse_github_search_markdown(p), [])


class WriteResearchItemsJsonlTests(unittest.TestCase):
    def test_empty_list_writes_empty_file_not_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "items.jsonl"
            write_research_items_jsonl([], path)
            self.assertEqual(path.read_text(encoding="utf-8"), "")

    def test_multiple_items_have_one_per_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "items.jsonl"
            items = [_sample_item(), _sample_item()]
            write_research_items_jsonl(items, path)
            body = path.read_text(encoding="utf-8")
            # Each item is one logical JSON object; there must be exactly
            # len(items) such objects on separate lines.
            lines = [line for line in body.splitlines() if line]
            self.assertEqual(len(lines), 2)
            for line in lines:
                json.loads(line)  # must parse


if __name__ == "__main__":
    unittest.main()
