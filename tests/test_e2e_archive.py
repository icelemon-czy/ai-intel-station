from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from library.backfill import backfill_output_tree
from library.items import (
    ResearchItem,
    build_github_repo_item,
    build_paper_item,
    write_research_item,
    write_research_items_jsonl,
)


class RealArchiveRoundTripTests(unittest.TestCase):
    """End-to-end: write real markdown + sidecars through the library, then
    read them back through the library + briefing pipeline. No mocks of
    collect/github, collect/papers, briefing.reports — we go through them.

    The "network-bound" helpers (``save_repo``, ``fetch_papers_by_category``)
    are deliberately NOT used; we synthesize their inputs by hand and let the
    on-disk pipeline (write_research_item → load_research_items → briefing)
    do the rest. This is the test layer that catches format drift.
    """

    def test_github_repo_sidecar_loads_via_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            repo_dir = output_root / "github" / "demo-demo-repo"
            repo_dir.mkdir(parents=True)
            md = repo_dir / "README.md"
            md.write_text(
                "# demo-repo\n\n> A demo repo for round-trip testing.\n\n"
                "- 🌐 URL: https://github.com/demo/demo-repo\n"
                "- ⭐ Stars: 123\n"
                "- 🏷️ Language: Python\n"
                "- 📅 Created: 2026-01-01\n"
                "- 🔄 Updated: 2026-06-15\n",
                encoding="utf-8",
            )
            data = {
                "name": "demo-repo",
                "description": "A demo repo for round-trip testing",
                "url": "https://github.com/demo/demo-repo",
                "stargazerCount": 123,
                "primaryLanguage": {"name": "Python"},
                "repositoryTopics": [{"topic": {"name": "demo"}}],
                "createdAt": "2026-01-01T00:00:00Z",
                "updatedAt": "2026-06-15T00:00:00Z",
                "issues": [],
            }
            item = build_github_repo_item("demo", "demo-repo", data, md)
            write_research_item(item, repo_dir / "research-item.json")

            # Read back through the loader.
            from library.storage import load_research_items

            items = load_research_items(output_root)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].title, "demo-repo")
            self.assertEqual(items[0].canonical_url, "https://github.com/demo/demo-repo")
            self.assertIn("demo", items[0].tags)
            self.assertEqual(items[0].metadata["stargazer_count"], 123)
            self.assertEqual(items[0].metadata["primary_language"], "Python")

    def test_paper_sidecar_loads_and_renders_in_briefing(self) -> None:
        """A real paper sidecar should appear in a generated briefing."""
        from briefing.service import build_generic_briefing_from_items, save_generic_briefing
        from library.query import query_research_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            paper_md = output_root / "papers" / "arXiv-cs.AI" / "01-Sample Paper.md"
            paper_md.parent.mkdir(parents=True)
            paper_md.write_text(
                "# Sample Paper on Round-Trip Testing\n\n"
                "> **Authors:** Alice, Bob\n\n"
                "- 📅 Published: 2026-06-01\n"
                "- 🏷️ Categories: cs.AI\n"
                "- 🔗 arXiv: https://arxiv.org/abs/2606.99999\n"
                "- 📄 PDF: https://arxiv.org/pdf/2606.99999\n\n"
                "## Abstract\n\nWe test that papers round-trip through the library and briefing.\n",
                encoding="utf-8",
            )
            paper = {
                "title": "Sample Paper on Round-Trip Testing",
                "authors": ["Alice", "Bob"],
                "summary": "We test round-trip.",
                "published": "2026-06-01T00:00:00Z",
                "updated": "2026-06-02T00:00:00Z",
                "arxiv_id": "2606.99999",
                "pdf_url": "https://arxiv.org/pdf/2606.99999",
                "abs_url": "https://arxiv.org/abs/2606.99999",
                "categories": ["cs.AI"],
            }
            write_research_item(
                build_paper_item(paper, paper_md),
                paper_md.with_name(paper_md.stem + ".research-item.json"),
            )

            # Query and briefing generation should both succeed without mocking.
            items = query_research_items(output_root, sources=["papers"])
            self.assertEqual(len(items), 1)

            briefing = build_generic_briefing_from_items(
                mode="digest", title="daily", items=items, requested_sources=["papers"]
            )
            digest_path = save_generic_briefing(briefing, output_root).path
            self.assertIsNotNone(digest_path)
            assert digest_path is not None
            content = digest_path.read_text(encoding="utf-8")
            self.assertIn("# Digest: daily", content)
            self.assertIn("Sample Paper on Round-Trip Testing", content)
            # Local link is either a relative path (when output is under REPO_ROOT)
            # or a file:// URI (when output lives elsewhere, e.g. /tmp in tests).
            self.assertTrue(
                "[open local](../../papers/arXiv-cs.AI/01-Sample Paper.md)" in content
                or "file://" in content,
                f"expected local link in:\n{content}",
            )

    def test_github_search_results_jsonl_loads(self) -> None:
        """Search results use JSONL sidecars; load_research_items handles both."""
        from collect.github import build_github_search_items
        from library.storage import load_research_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            search_dir = output_root / "github" / "agent-harness"
            search_dir.mkdir(parents=True)
            (search_dir / "search.md").write_text(
                "# Search: agent harness\n\nFound 2 repositories\n",
                encoding="utf-8",
            )
            repos = [
                {"name": "alpha", "url": "https://github.com/a/alpha", "stargazersCount": 100,
                 "description": "alpha repo", "owner": {"login": "a"}},
                {"name": "beta", "url": "https://github.com/b/beta", "stargazersCount": 50,
                 "description": "beta repo", "owner": {"login": "b"}},
            ]
            items = build_github_search_items("agent harness", repos, search_dir / "search.md")
            write_research_items_jsonl(items, search_dir / "research-items.jsonl")

            loaded = load_research_items(output_root)
            self.assertEqual(len(loaded), 2)
            titles = {i.title for i in loaded}
            self.assertEqual(titles, {"alpha", "beta"})

    def test_backfill_creates_sidecars_for_historical_markdown(self) -> None:
        """A directory of legacy markdown (no sidecars) becomes queryable."""
        from library.storage import load_research_items

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            github_dir = output_root / "github" / "legacy-owner-legacy-repo"
            github_dir.mkdir(parents=True)
            (github_dir / "README.md").write_text(
                "# legacy-repo\n\n> A legacy repository.\n\n"
                "- 🌐 URL: https://github.com/legacy-owner/legacy-repo\n"
                "- ⭐ Stars: 42\n"
                "- 🏷️ Language: Go\n"
                "- 📅 Created: 2025-01-01\n"
                "- 🔄 Updated: 2025-12-01\n",
                encoding="utf-8",
            )

            written = backfill_output_tree(output_root)
            self.assertEqual(len(written), 1)
            self.assertTrue(written[0].is_file())

            items = load_research_items(output_root)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0].title, "legacy-repo")
            self.assertEqual(items[0].metadata["stargazer_count"], 42)


if __name__ == "__main__":
    unittest.main()

# ---------------------------------------------------------------------------
# Contract Requirement: Source-Segregated Archive
# "All generated artifacts SHALL be written to source-specific subdirectories
#  under output/."
# We walk the resulting tree and assert no file leaked outside the
# source-specific subdirectory. This is a negative assertion (no escape)
# that the previous archive tests didn't make explicit.
# ---------------------------------------------------------------------------


class ContractSourceSegregatedArchiveTests(unittest.TestCase):
    """For each source, build a real artifact and walk the resulting tree
    to assert no file leaked outside the source-specific subdirectory."""

    def _assert_no_escape(self, output_root, source_subdir):
        from pathlib import Path
        expected_prefix = (Path(output_root) / source_subdir).resolve()
        for path in Path(output_root).rglob("*"):
            if not path.is_file():
                continue
            if path.resolve().is_relative_to(expected_prefix):
                continue
            # briefing/ is the only legitimate cross-cutting output dir.
            if "briefing" in path.parts:
                continue
            self.fail(
                f"file leaked outside {source_subdir}: {path}"
            )

    def test_github_writes_only_under_output_github(self):
        from library.items import build_github_repo_item, write_research_item

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            repo_dir = output_root / "github" / "demo-demo"
            repo_dir.mkdir(parents=True)
            (repo_dir / "README.md").write_text("# demo\n", encoding="utf-8")
            item = build_github_repo_item(
                "demo", "demo",
                {
                    "name": "demo",
                    "description": "test",
                    "url": "https://github.com/demo/demo",
                    "stargazerCount": 1,
                    "primaryLanguage": {"name": "Go"},
                    "repositoryTopics": [],
                    "createdAt": "2026-01-01T00:00:00Z",
                    "updatedAt": "2026-01-01T00:00:00Z",
                    "issues": [],
                },
                repo_dir / "README.md",
            )
            write_research_item(item, repo_dir / "research-item.json")
            self._assert_no_escape(output_root, "github")

    def test_papers_writes_only_under_output_papers(self):
        from library.items import build_paper_item, write_research_item

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            papers_dir = output_root / "papers" / "arXiv-cs.AI"
            papers_dir.mkdir(parents=True)
            md = papers_dir / "test.md"
            md.write_text("# t\n", encoding="utf-8")
            item = build_paper_item(
                {
                    "title": "t",
                    "authors": ["a"],
                    "summary": "s",
                    "published": "2026-01-01T00:00:00Z",
                    "updated": "2026-01-01T00:00:00Z",
                    "arxiv_id": "2606.00001",
                    "pdf_url": "https://arxiv.org/pdf/2606.00001",
                    "abs_url": "https://arxiv.org/abs/2606.00001",
                    "categories": ["cs.AI"],
                },
                md,
            )
            write_research_item(item, md.with_name(md.stem + ".research-item.json"))
            self._assert_no_escape(output_root, "papers")


# ---------------------------------------------------------------------------
# Contract Requirement: Traceable Markdown Artifacts
# "Every generated Markdown artifact SHALL preserve enough metadata to
#  identify the original source."
# Real e2e: build the item via the real builder and assert the sidecar
# preserves canonical_url + publication metadata.
# ---------------------------------------------------------------------------


class ContractTraceableArtifactsTests(unittest.TestCase):
    def test_github_repo_markdown_preserves_canonical_url(self):
        from library.items import build_github_repo_item

        with tempfile.TemporaryDirectory() as tmp:
            repo_dir = Path(tmp) / "github" / "demo-demo"
            repo_dir.mkdir(parents=True)
            (repo_dir / "README.md").write_text(
                "# demo\n\n> A demo repo.\n\n"
                "- 🌐 URL: https://github.com/demo/demo\n"
                "- ⭐ Stars: 7\n"
                "- 🏷️ Language: Python\n"
                "- 📅 Created: 2026-01-01\n"
                "- 🔄 Updated: 2026-06-15\n",
                encoding="utf-8",
            )
            item = build_github_repo_item(
                "demo", "demo",
                {
                    "name": "demo",
                    "description": "A demo repo for round-trip testing",
                    "url": "https://github.com/demo/demo",
                    "stargazerCount": 7,
                    "primaryLanguage": {"name": "Python"},
                    "repositoryTopics": [],
                    "createdAt": "2026-01-01T00:00:00Z",
                    "updatedAt": "2026-06-15T00:00:00Z",
                    "issues": [],
                },
                repo_dir / "README.md",
            )
            self.assertEqual(
                item.canonical_url, "https://github.com/demo/demo",
                "github item must preserve the source URL for traceability",
            )
            self.assertEqual(item.metadata["stargazer_count"], 7)
            self.assertEqual(item.metadata["primary_language"], "Python")

    def test_paper_markdown_preserves_arxiv_urls(self):
        from library.items import build_paper_item

        with tempfile.TemporaryDirectory() as tmp:
            papers_dir = Path(tmp) / "papers" / "arXiv-cs.AI"
            papers_dir.mkdir(parents=True)
            md = papers_dir / "01-paper.md"
            md.write_text(
                "# Sample paper\n\n"
                "> **Authors:** Alice\n\n"
                "- 📅 Published: 2026-06-01\n"
                "- 🏷️ Categories: cs.AI\n"
                "- 🔗 arXiv: https://arxiv.org/abs/2606.99999\n"
                "- 📄 PDF: https://arxiv.org/pdf/2606.99999\n\n"
                "## Abstract\n\nTest.\n",
                encoding="utf-8",
            )
            item = build_paper_item(
                {
                    "title": "Sample paper",
                    "authors": ["Alice"],
                    "summary": "Test.",
                    "published": "2026-06-01T00:00:00Z",
                    "updated": "2026-06-02T00:00:00Z",
                    "arxiv_id": "2606.99999",
                    "pdf_url": "https://arxiv.org/pdf/2606.99999",
                    "abs_url": "https://arxiv.org/abs/2606.99999",
                    "categories": ["cs.AI"],
                },
                md,
            )
            self.assertEqual(
                item.canonical_url, "https://arxiv.org/abs/2606.99999",
            )
            self.assertEqual(
                item.metadata["pdf_url"], "https://arxiv.org/pdf/2606.99999",
            )
            self.assertEqual(item.published_at, "2026-06-01T00:00:00Z")
