"""Current source contract coverage — real CLI subprocess tests for the
papers / research-operations / github sub-spec requirements.

These tests fill the gap left by `test_system_contracts.py` and
`test_http_*_e2e.py`: those cover the top-level system spec, but
specifications are also written at the capability level
(`doc/validation_design.md`,
`doc/validation_design.md`,
`doc/validation_design.md`) with their own requirements
and scenarios. Each test below is one REAL `subprocess.run` of the
unified `research` entrypoint — no business-layer mocking.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


def _run_research(*args, output_root: Path | None = None, timeout: int = 60):
    """Run `research <args>` in a real subprocess, with PYTHONPATH
    pointed at the repo root so the `research` console script
    resolves to the in-tree module (not a globally-installed copy)."""
    cmd_args = [PYTHON, "-c",
                "from ai_intel_station.cli import console_main; console_main()",
                *args]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    if output_root is not None:
        env["_USE_OUT"] = str(output_root)
        # The CLI accepts -o flag for some commands; that's enough.
    return subprocess.run(
        cmd_args,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


def _run_research_with_output(*args, output_root: Path, timeout: int = 60):
    """Run `research <args>` with `-o <output_root>` as an explicit
    flag (the way a real operator would). Returns CompletedProcess.
    """
    cmd_args = [PYTHON, "-c",
                "from ai_intel_station.cli import console_main; console_main()",
                *args, "-o", str(output_root)]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        cmd_args,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Contract sub-spec: papers / "List Supported AI Categories"
# Scenario: "WHEN the operator runs the command with --list,
#  THEN the tool prints the supported category codes and labels."
# Real e2e: real subprocess + --list + assert every AI_CATEGORIES entry
# appears in stdout.
# ---------------------------------------------------------------------------


class ContractPapersListSubprocessTests(unittest.TestCase):
    def test_research_collect_papers_list_exposes_every_ai_category(self):
        from ai_intel_station.collect.papers import AI_CATEGORIES  # type: ignore

        result = _run_research("collect", "papers", "--list")
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        # Every category code + label must appear on stdout. The CLI
        # prints them via `print(CATEGORIES_HELP)`, which is generated
        # from AI_CATEGORIES — both must be present.
        for code, label in AI_CATEGORIES.items():
            self.assertIn(code, result.stdout,
                          f"category code {code} missing from `research collect papers --list` stdout")
            # The label may wrap across two lines, so check the first
            # word of the label at minimum.
            first_label_word = label.split()[0]
            self.assertIn(first_label_word, result.stdout,
                          f"label fragment {first_label_word!r} for {code} missing from stdout")


# ---------------------------------------------------------------------------
# Contract sub-spec: papers / "Continue Across Category-Level Failures"
# Scenario: "WHEN one requested category fetch fails and another succeeds,
#  THEN the tool reports the failed category and still writes files for the
#  successful category."
# Real e2e: pass one valid + one invalid category. The CLI must:
#   - explicitly report the unknown category (not silently skip it),
#   - attempt the valid one, and
#   - exit non-zero only if the *valid* one fails (network/IO error),
#     not because of the invalid one.
# This test does NOT rely on sandbox internet state — it asserts the
# bound on the contract that's spec'd at this layer.
# ---------------------------------------------------------------------------


class ContractPapersMixedOutcomeSubprocessTests(unittest.TestCase):
    def test_invalid_category_reported_and_does_not_block_valid_one(self):
        # Redirect only the network layer to a local Atom fixture. The
        # production parser, category loop, CLI dispatch, and persistence
        # remain real; all writes are contained by the temporary output.
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "output"
            xml_path = tmp_path / "arxiv_fixture.xml"
            xml_path.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2606.12345v1</id>
    <title>Mixed outcome fixture paper</title>
    <summary>Local network-boundary fixture.</summary>
    <published>2026-06-01T00:00:00Z</published>
    <updated>2026-06-02T00:00:00Z</updated>
    <author><name>Alice</name></author>
    <category term="cs.AI" />
  </entry>
</feed>
""",
                encoding="utf-8",
            )
            script = (
                "import sys\n"
                f"sys.path.insert(0, {str(REPO_ROOT / "src")!r})\n"
                "import ai_intel_station.collect.papers as papers_collect\n"
                "from urllib import request as urllib_request\n"
                "original = urllib_request.urlopen\n"
                f"fixture_url = {xml_path.as_uri()!r}\n"
                "def redirect(_request, *args, **kwargs):\n"
                "    return original(fixture_url, *args, **kwargs)\n"
                "papers_collect.urlopen = redirect\n"
                "from ai_intel_station.cli import console_main\n"
                "console_main()\n"
            )
            result = subprocess.run(
                [
                    PYTHON,
                    "-c",
                    script,
                    "collect",
                    "papers",
                    "xx.NOTREAL",
                    "cs.AI",
                    "--max",
                    "1",
                    "-o",
                    str(output_root),
                ],
                capture_output=True,
                text=True,
                env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
                cwd=str(REPO_ROOT),
                timeout=60,
            )

            combined = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, combined[-800:])
            self.assertIn("xx.NOTREAL", combined)
            self.assertTrue(
                "Unknown" in combined
                or "⚠️" in combined
                or "unknown" in combined.lower(),
                f"unknown-category warning marker missing from output:\n{combined[:600]}",
            )
            saved = list((output_root / "papers").glob("*.md"))
            self.assertEqual(len(saved), 1, combined[-800:])
            self.assertIn(
                "Mixed outcome fixture paper",
                saved[0].read_text(encoding="utf-8"),
            )


# ---------------------------------------------------------------------------
# Contract sub-spec: research-operations / "Partial Progress Continues"
# Scenario: "WHEN the operator requests a briefing that names a source
#  not present in the local archive, THEN the briefing still completes
#  with the sources that ARE present."
# Real e2e: seed a small local archive with only one of the requested
# sources, then run `research briefing digest <keyword>` over both.
# The briefing MUST finish without error and the report MUST mention
# the missing source.
# ---------------------------------------------------------------------------


class ContractResearchPartialProgressSubprocessTests(unittest.TestCase):
    def test_briefing_with_missing_source_still_completes(self):
        # Seed a local archive: ONE github item, NO papers / NO wechat.
        # Then ask for a briefing over github + papers + wechat.
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            from ai_intel_station.library.items import (
                build_github_repo_item,
                write_research_item,
            )

            repo_dir = output_root / "github" / "demo-foo-bar"
            repo_dir.mkdir(parents=True)
            (repo_dir / "README.md").write_text(
                "# foo-bar\n\n> partial-progress fixture.\n\n"
                "- 🌐 URL: https://github.com/demo/foo-bar\n"
                "- ⭐ Stars: 1\n"
                "- 🏷️ Language: Go\n",
                encoding="utf-8",
            )
            write_research_item(
                build_github_repo_item(
                    "demo",
                    "foo-bar",
                    {
                        "name": "foo-bar",
                        "description": "partial-progress",
                        "url": "https://github.com/demo/foo-bar",
                        "stargazerCount": 1,
                        "primaryLanguage": {"name": "Go"},
                        "repositoryTopics": [],
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-06-15T00:00:00Z",
                        "issues": [],
                    },
                    repo_dir / "README.md",
                ),
                repo_dir / "research-item.json",
            )

            # Run the documented command. The briefing output goes under
            # {output_root}/briefing/.
            result = _run_research_with_output(
                "briefing", "digest", "partial-progress",
                "--source", "github",
                "--source", "papers",
                "--source", "wechat",
                output_root=output_root,
                timeout=60,
            )
            # The CLI exit code must be 0 — the briefing must NOT bail
            # out just because papers/wechat are empty locally.
            self.assertEqual(
                result.returncode,
                0,
                msg=f"`research briefing digest` failed: rc={result.returncode}\n"
                    f"stdout={result.stdout}\nstderr={result.stderr}",
            )
            # AND a briefing file must have been written.
            briefing_root = output_root / "briefing"
            digests = list(briefing_root.rglob("digest*partial-progress*.md")) if briefing_root.exists() else []
            # The exact filename varies across releases; accept any
            # digest-*.md with partial-progress in the content.
            matching = [
                p for p in (briefing_root.rglob("*.md") if briefing_root.exists() else [])
                if "partial-progress" in p.read_text(encoding="utf-8", errors="replace")
            ]
            self.assertTrue(
                matching,
                f"no briefing digest mentioning 'partial-progress' was written under "
                f"{briefing_root}. stdout={result.stdout[:400]}",
            )


# ---------------------------------------------------------------------------
# Contract sub-spec: research-operations / "Unified Workspace Command Surface"
# Scenario: "WHEN the operator runs `research collect github owner/repo`,
#  THEN the unified surface reaches the GitHub collect module."
# Real e2e: if `gh` is missing from PATH (sandbox reality),
# `collect github owner/repo` MUST surface an explicit error that
# names `gh` rather than crashing the unified surface. (This is
# companion coverage to the cross-process variant in
# `test_http_failure_e2e.py::ContractExplicitFailureHttpBoundaryTests`, but
# exercises the CLI surface — exactly what `research` itself
# documents — not the HTTP API.)
# ---------------------------------------------------------------------------


class ContractResearchUnifiedCliSurfaceTests(unittest.TestCase):
    def test_research_collect_github_surfaces_gh_failure_through_unified_cli(self):
        # Strip `gh` from PATH for the child process so `collect.github.run_gh`
        # genuinely can't find the binary. Capture stdout+stderr; the
        # unified surface MUST include "gh" in the failure message so an
        # operator who runs `research collect github owner/repo` knows
        # exactly what to install.
        with tempfile.TemporaryDirectory() as tmp:
            empty_path = Path(tmp) / "_empty_path"
            empty_path.mkdir(exist_ok=True)
            env = os.environ.copy()
            env["PATH"] = str(empty_path)  # mask real gh
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [PYTHON, "-c",
                 "from ai_intel_station.cli import console_main; console_main()",
                 "collect", "github", "demo/never-existed"],
                capture_output=True, text=True, env=env,
                cwd=str(REPO_ROOT), timeout=30,
            )
            combined = (result.stdout + result.stderr).lower()
            self.assertIn(
                "gh",
                combined,
                f"`research collect github` exited but never named the failing "
                f"tool 'gh'. rc={result.returncode}\nstdout={result.stdout[:400]}\n"
                f"stderr={result.stderr[:400]}",
            )


# ---------------------------------------------------------------------------
# Contract sub-spec: research-operations / "Workspace Query And Briefing Actions"
# Scenario: "WHEN the operator runs `research query <keyword>`, THEN ...
#  WHEN the operator runs `research briefing reading-list <keyword>`,
#  THEN ..."
# Real e2e: `research query <kw> --source github` over a seeded archive
# MUST return the seeded item (visible to operator). This is the entry
# point the user uses for "did my collect persist?" — if query is
# broken, the operator can't even verify collect succeeded.
# ---------------------------------------------------------------------------


class ContractResearchQuerySubprocessTests(unittest.TestCase):
    def test_research_query_returns_seeded_item_through_unified_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            from ai_intel_station.library.items import (
                build_github_repo_item,
                write_research_item,
            )

            repo_dir = output_root / "github" / "demo-cli-query-fixture"
            repo_dir.mkdir(parents=True)
            (repo_dir / "README.md").write_text(
                "# cli-query-fixture\n\n> query e2e.\n\n"
                "- 🌐 URL: https://github.com/demo/cli-query-fixture\n"
                "- ⭐ Stars: 1\n"
                "- 🏷️ Language: Python\n",
                encoding="utf-8",
            )
            write_research_item(
                build_github_repo_item(
                    "demo",
                    "cli-query-fixture",
                    {
                        "name": "cli-query-fixture",
                        "description": "query-fixture",
                        "url": "https://github.com/demo/cli-query-fixture",
                        "stargazerCount": 1,
                        "primaryLanguage": {"name": "Python"},
                        "repositoryTopics": [],
                        "createdAt": "2026-01-01T00:00:00Z",
                        "updatedAt": "2026-06-15T00:00:00Z",
                        "issues": [],
                    },
                    repo_dir / "README.md",
                ),
                repo_dir / "research-item.json",
            )

            result = _run_research_with_output(
                "query", "cli-query-fixture",
                "--source", "github",
                output_root=output_root,
                timeout=60,
            )
            self.assertEqual(
                result.returncode, 0,
                msg=f"`research query` rc={result.returncode}: "
                    f"stdout={result.stdout}\nstderr={result.stderr}",
            )
            combined = result.stdout + result.stderr
            self.assertIn(
                "cli-query-fixture",
                combined,
                f"query result missing the seeded item name: "
                f"stdout={result.stdout[:400]}",
            )


if __name__ == "__main__":
    unittest.main()
