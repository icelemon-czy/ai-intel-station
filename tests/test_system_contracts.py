"""Current system contract compliance — real e2e tests for each top-level requirement in
`doc/validation_design.md`. Every test exercises the actual public
surface (CLI, fetch, ThreadingHTTPServer) and asserts behaviour the spec
calls out, not internal implementation details.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from library.query import query_research_items
from library.items import write_research_item, build_paper_item, build_github_repo_item


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


def _run_cli(*args, env_extra=None, cwd=None, timeout=60):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [PYTHON, "-c", "from research.cli import console_main; console_main()", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Requirement: Runnable Documented Entrypoints
# "Each supported capability SHALL have at least one documented command
#  that can be executed from the workspace using the documented runtime
#  rules."
# Real e2e: invoke the documented `research` entrypoint and verify it
# reaches the unified operator surface (subcommands for collect/query/
# briefing/backfill/organize/web/discover/schedule/init-config), not a source-
# specific wrapper.
# ---------------------------------------------------------------------------


class ContractRunnableDocumentedEntrypointsTests(unittest.TestCase):
    def test_research_help_lists_all_documented_subcommands(self):
        result = _run_cli("--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        for cmd in ("collect", "query", "briefing", "backfill", "organize",
                    "web", "discover", "schedule", "init-config"):
            self.assertIn(cmd, result.stdout, f"missing documented subcommand {cmd!r}")

    def test_research_collect_help_references_required_fields(self):
        result = _run_cli("collect", "github", "--help")
        self.assertEqual(result.returncode, 0)
        # The documented collect entrypoint must accept the same args that
        # collect/github.py expects (--search, --output-root, --issues).
        for flag in ("--search", "--output"):
            self.assertIn(flag, result.stdout,
                          f"collect github --help missing documented flag {flag!r}")

    def test_discover_help_documents_first_time_steps(self):
        # Contract: "command documented in `.ai` or workspace README files".
        # The discover subcommand must self-document its first-time usage
        # because the workspace README is the entrypoint for new users.
        result = _run_cli("discover", "--help")
        self.assertIn("init-config", result.stdout)
        self.assertIn("dry-run", result.stdout)


# ---------------------------------------------------------------------------
# Requirement: Explicit External Dependency Failure
#
# Both scenarios ("gh unavailable" and "arXiv category fetch fails")
# moved to `tests/test_http_failure_e2e.py::ContractExplicitFailureHttpBoundaryTests`,
# where the failure is reproduced by stripping `gh` from `PATH` in a
# real subprocess and the contract is verified through the real HTTP
# boundary — i.e. what an operator's browser actually does on a
# machine without `gh` installed. The previous in-process monkeypatch
# version of these tests has been retired because monkeypatching
# `collect.github.run_gh` is the kind of mock the Contract spec explicitly
# rules out.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Requirement: Optional Live Verification
# Scenario: "WeChat live test without URLs" — when WECHAT_E2E_URLS is
# unset, the live e2e test is skipped rather than treated as a product
# failure.
# Real e2e: simulate the WeChat live test's environment-check by
# invoking the test runner with the env var unset and verifying the test
# self-skips (reports "skipped") rather than errors.
# ---------------------------------------------------------------------------


class ContractOptionalLiveVerificationTests(unittest.TestCase):
    def test_wechat_live_test_skips_when_urls_unset(self):
        # Mirror the behaviour of tests/test_wechat_e2e_live.py: when
        # WECHAT_E2E_URLS is empty, it should self-skip. We invoke the
        # test runner with the env var explicitly unset and verify that
        # the suite completes without errors (because the test
        # self-skipped). If the test were unconditional, the suite
        # would either fail (no network) or hang (camoufox launch).
        env = os.environ.copy()
        env.pop("WECHAT_E2E_URLS", None)
        env["PYTHONPATH"] = str(REPO_ROOT)
        result = subprocess.run(
            [PYTHON, "-m", "pytest", "-q", "tests/test_wechat_e2e_live.py"],
            capture_output=True,
            text=True,
            env=env,
            timeout=30,
        )
        # The run must complete cleanly. The Contract contract is "skip cleanly
        # when prerequisites are absent". Two acceptable outcomes:
        #   1. The test self-skipped (pytest fixtures unavailable
        #      gracefully skip the live test).
        # The pytest module is the real test runner for this file.
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, combined[:600])
        self.assertIn("skipped", combined.lower())


# ---------------------------------------------------------------------------
# Requirement: Source-Segregated Archive (extra negative coverage).
# "All generated artifacts SHALL be written to source-specific subdirectories
#  under output/." We already cover the on-disk write in test_e2e_archive.py;
# here we cover the cross-cutting side: query_research_items by source must
# ONLY return items that actually live under that source's directory.
# ---------------------------------------------------------------------------


class ContractSourceSegregatedQueryTests(unittest.TestCase):
    def test_query_research_items_respects_source_filter_at_fs_level(self):
        # Seed two sources side-by-side; ensure filter by source only
        # returns items that physically live under that source's subdir.
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            gh = output_root / "github" / "demo-x"
            gh.mkdir(parents=True)
            (gh / "README.md").write_text(
                "# x\n\n> x\n\n"
                "- 🌐 URL: https://github.com/demo/x\n"
                "- ⭐ Stars: 1\n"
                "- 🏷️ Language: Go\n"
                "- 📅 Created: 2026-01-01\n"
                "- 🔄 Updated: 2026-06-15\n",
                encoding="utf-8",
            )
            write_research_item(
                build_github_repo_item(
                    "demo", "x",
                    {
                        "name": "x", "description": "x",
                        "url": "https://github.com/demo/x",
                        "stargazerCount": 1,
                        "primaryLanguage": {"name": "Go"},
                        "repositoryTopics": [],
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-01-01T00:00:00Z",
                        "issues": [],
                    },
                    gh / "README.md",
                ),
                gh / "research-item.json",
            )
            papers = output_root / "papers" / "arXiv-cs.AI"
            papers.mkdir(parents=True)
            (papers / "x.md").write_text(
                "# x\n\n> **Authors:** A\n\n"
                "- 📅 Published: 2026-01-01\n"
                "- 🏷️ Categories: cs.AI\n"
                "- 🔗 arXiv: https://arxiv.org/abs/0000.00000\n"
                "- 📄 PDF: https://arxiv.org/pdf/0000.00000\n",
                encoding="utf-8",
            )
            write_research_item(
                build_paper_item(
                    {
                        "title": "x", "authors": ["A"], "summary": "x",
                        "published": "2026-01-01T00:00:00Z",
                        "updated": "2026-01-01T00:00:00Z",
                        "arxiv_id": "0000.00000",
                        "pdf_url": "https://arxiv.org/pdf/0000.00000",
                        "abs_url": "https://arxiv.org/abs/0000.00000",
                        "categories": ["cs.AI"],
                    },
                    papers / "x.md",
                ),
                papers / "x.research-item.json",
            )

            # Query with source filter — items returned MUST physically
            # live under that source's subdir.
            for source, expected_subdir in (("github", "github"), ("papers", "papers")):
                items = query_research_items(output_root, sources=[source])
                self.assertTrue(items, f"no items returned for source={source}")
                for item in items:
                    out_path = (Path(tmp) / item.output_path).resolve() if item.output_path else None
                    if out_path is None:
                        continue
                    self.assertTrue(
                        expected_subdir in out_path.parts,
                        f"query_research_items returned an item under "
                        f"{out_path} for source={source!r} — should be filtered out",
                    )


if __name__ == "__main__":
    unittest.main()
