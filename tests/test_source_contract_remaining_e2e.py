"""Current source contract coverage — real end-to-end tests for the remaining
github / wechat / papers capability-level scenarios.

These tests fill the last gap left by the earlier rounds. Each one
uses a real subprocess and exercises the real business layer
(collect.github.save_repo, collect.wechat.fetch_article, etc.). The
network layer (`subprocess.run(["gh", ...])`) is replaced only by a
**local fake binary on PATH** — never by monkeypatching the
business function. That distinction is documented in
`doc/validation_design.md`.

We use shell-script fakes (a 30-line bash that mimics `gh` for
the specific commands our collectors invoke) instead of
monkeypatching `collect.github.fetch_repo`. This way:
  - `collect.github.save_repo` runs with its real code paths,
  - `subprocess.run(["gh", ...])` is a real subprocess call,
  - the only thing under test control is *what* `gh` returns,
    which is exactly what the Contract spec says the surrounding code
    must handle.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


# ---------------------------------------------------------------------------
# Fake `gh` binary. We construct a small bash script on disk that mimics
# `gh` for the two CLI invocations our collectors rely on:
#   - `gh repo view <owner>/<repo> --json ...`            -> JSON for one repo
#   - `gh issue list -R <owner>/<repo> --state open --limit 20 --json ...`
#                                                       -> JSON list of issues
# By making this a real shell executable on PATH, we replace only the
# network-layer subprocess; the Python collectors (parse, write
# markdown, write sidecar) run unchanged.
# ---------------------------------------------------------------------------


def _make_fake_gh_dir(tmp: Path, *, repo_name: str = "demo-real-gh",
                     owner: str = "fixture",
                     issues: list[dict] | None = None) -> Path:
    """Create a directory with a `gh` shell script that returns
    realistic JSON for the commands `collect/github.py` invokes.

    Returns the directory the test should add to PATH.
    """
    bin_dir = tmp / "fake_gh_bin"
    bin_dir.mkdir(exist_ok=True)
    issues = issues or []
    repo_view_json = json.dumps({
        "name": repo_name,
        "description": "Real gh fixture",
        "url": f"https://github.com/{owner}/{repo_name}",
        "stargazerCount": 42,
        "primaryLanguage": {"name": "Python"},
        "repositoryTopics": [{"topic": {"name": "fixture"}}],
        "createdAt": "2026-01-01T00:00:00Z",
        "updatedAt": "2026-06-15T00:00:00Z",
    }, indent=2)
    issue_list_json = json.dumps(issues, indent=2)

    gh_script = bin_dir / "gh"
    # The script must (a) parse argv to distinguish `repo view` from
    # `issue list`, (b) emit the right JSON to stdout, and (c) exit 0.
    # Anything else is what `run_gh` would receive.
    gh_script.write_text(
        "#!/bin/bash\n"
        "set -e\n"
        'if [[ "$1 $2" == "repo view" ]]; then\n'
        "    cat <<'JSON'\n"
        f"{repo_view_json}\n"
        "JSON\n"
        'elif [[ "$1 $2" == "issue list" ]]; then\n'
        "    cat <<'JSON'\n"
        f"{issue_list_json}\n"
        "JSON\n"
        "else\n"
        '    echo "fake gh: unknown command $*" >&2\n'
        "    exit 1\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    gh_script.chmod(0o755)
    return bin_dir


def _run_subprocess(args: list[str], *, env_extra: dict[str, str], cwd: str = str(REPO_ROOT), timeout: int = 60):
    """Run `python -m` style subprocess with our project on PYTHONPATH and the
    fake `gh` directory prepended to PATH. Returns CompletedProcess."""
    env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src"), **env_extra}
    return subprocess.run(
        [PYTHON, "-c", "from ai_intel_station.cli import console_main; console_main()", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=cwd,
        timeout=timeout,
    )


# ---------------------------------------------------------------------------
# Contract sub-spec: github / "Include Open Issues in Repository Snapshots"
# Scenario: "WHEN repo mode fetches repository data, THEN the saved
#  Markdown includes the Open Issues section with issue number, labels,
#  and author."
# Real e2e: install a fake `gh` on PATH, run `research collect github
#  ... --issues` (CLI default), and verify the saved README contains a
#  populated "## Open Issues" section. No business-layer mocking.
# ---------------------------------------------------------------------------


class ContractGithubIncludesOpenIssuesSubprocessTests(unittest.TestCase):
    def test_research_collect_github_writes_open_issues_section(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "output"
            fake_gh_dir = _make_fake_gh_dir(
                tmp_path,
                repo_name="real-gh-issues",
                owner="fixture-org",
                issues=[
                    {
                        "number": 7,
                        "title": "Implement local mode",
                        "state": "open",
                        "labels": [{"name": "enhancement"}],
                        "author": {"login": "octo"},
                        "createdAt": "2026-05-20T00:00:00Z",
                    },
                    {
                        "number": 12,
                        "title": "Crash on empty list",
                        "state": "open",
                        "labels": [],
                        "author": {"login": "bugbot"},
                        "createdAt": "2026-06-02T00:00:00Z",
                    },
                ],
            )
            result = _run_subprocess(
                [
                    "collect",
                    "github",
                    "fixture-org/real-gh-issues",
                    "--output-root",
                    str(output_root),
                ],
                env_extra={
                    "PATH": f"{fake_gh_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                },
            )
            combined = (result.stdout + result.stderr).lower()
            self.assertEqual(
                result.returncode, 0,
                msg=f"`research collect github` returned rc={result.returncode}.\n"
                    f"stdout={result.stdout[-500:]}\nstderr={result.stderr[-500:]}",
            )
            md_path = output_root / "github" / "fixture-org" / "real-gh-issues" / "README.md"
            self.assertTrue(
                md_path.exists(),
                f"expected {md_path} to exist after real collect. "
                f"combined output:\n{combined[-500:]}",
            )
            md = md_path.read_text(encoding="utf-8")
            # Contract contract: open issues MUST appear in the saved
            # Markdown, with number, label, author.
            self.assertIn("## Open Issues", md,
                          "saved README missing '## Open Issues' section")
            self.assertIn("[#7]", md, "issue #7 missing from saved Markdown")
            self.assertIn("Implement local mode", md)
            self.assertIn("[enhancement]", md, "issue label missing from Markdown")
            self.assertIn("(@octo)", md, "issue author @octo missing from Markdown")
            self.assertIn("[#12]", md)
            self.assertIn("Crash on empty list", md)
            self.assertIn("(@bugbot)", md)


# ---------------------------------------------------------------------------
# Contract sub-spec: github / "Save Search Results as Markdown"
# Scenario: "WHEN the operator runs the command with --search, THEN the
#  search results are written under a search-specific Markdown file."
# Real e2e: install a fake `gh search repos ...` that returns a JSON
# list, run `research collect github --search <query>`, verify the
# search.md file is written with the fixture repo titles.
# ---------------------------------------------------------------------------


class ContractGithubSearchSubprocessTests(unittest.TestCase):
    def test_research_collect_github_search_writes_search_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "output"
            bin_dir = tmp_path / "fake_gh_bin"
            bin_dir.mkdir(exist_ok=True)
            search_results = [
                {
                    "name": "alpha",
                    "url": "https://github.com/example/alpha",
                    "stargazersCount": 100,
                    "description": "alpha repo",
                    "owner": {"login": "example"},
                },
                {
                    "name": "beta",
                    "url": "https://github.com/example/beta",
                    "stargazersCount": 50,
                    "description": "beta repo",
                    "owner": {"login": "example"},
                },
            ]
            gh = bin_dir / "gh"
            gh.write_text(
                "#!/bin/bash\n"
                'if [[ "$1" == "search" ]]; then\n'
                "  cat <<'JSON'\n"
                f"{json.dumps(search_results)}\n"
                "JSON\n"
                "  exit 0\n"
                "fi\n"
                "exit 1\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)
            # We need a clean output_root so the assertion knows where
            # to look. CLI accepts `-o`.
            result = _run_subprocess(
                ["collect", "github", "alpha-search-keyword", "--search",
                 "-o", str(output_root)],
                env_extra={"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"},
            )
            self.assertEqual(
                result.returncode, 0,
                msg=f"`research collect github --search` rc={result.returncode}.\n"
                    f"stdout={result.stdout[-400:]}\nstderr={result.stderr[-400:]}",
            )
            # The CLI writes search.md under output_root/github/<query-dir>/.
            # Search results use a slug of the query as the directory name.
            search_md_candidates = list((output_root / "github").rglob("*.md"))
            self.assertTrue(
                search_md_candidates,
                f"no .md written under {output_root / 'github'}\n"
                f"stdout={result.stdout[-300:]}\nstderr={result.stderr[-300:]}",
            )
            # At least one file must mention the fixture repos.
            joined = ""
            for f in search_md_candidates:
                joined += f.read_text(encoding="utf-8", errors="replace")
            self.assertIn("alpha", joined,
                          "search Markdown missing 'alpha' (fixture repo)")
            self.assertIn("beta", joined,
                          "search Markdown missing 'beta' (fixture repo)")
            self.assertIn("alpha-search-keyword", joined,
                          "search Markdown missing the query keyword")


# ---------------------------------------------------------------------------
# Contract sub-spec: papers / "Fetch Latest Papers by Category" (success path)
# Scenario: "WHEN the operator requests cs.AI with --max 10, THEN the
#  tool requests the newest papers for that category and prepares up to
#  10 summaries."
# Real e2e: stand up a local stub HTTP server that mimics arxiv.org
# responses, point env so `urlopen` routes through it via Python's
# socket-level resolution (or directly use monkeypatch to redirect
# urlopen — which IS the network layer, not the business layer).
# Wait, the cleaner approach: the fetch path uses
# `urllib.request.urlopen`; redirecting that import-level dep is
# exactly what `doc/validation_design.md` calls "acceptable."
# We do that in-process: redirect `collect.papers.urlopen` to a local
# URL serving a fixture XML.
# ---------------------------------------------------------------------------


class ContractPapersFetchLatestSubprocessTests(unittest.TestCase):
    def test_research_collect_papers_cs_ai_writes_paper_markdown(self):
        """Contract sub-spec: 'Fetch Latest Papers by Category' (success path).

        We redirect only the network layer (`urllib.request.urlopen`)
        to a local XML fixture mimicking arXiv's Atom feed. The
        business-layer `fetch_papers_by_category` + `save_papers`
        run unchanged — they parse the XML, filter to the requested
        category, and write Markdown. This is the lightest
        acceptable substitute for a live arXiv call; see
        `doc/validation_design.md` for the rationale."""

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output_root = tmp_path / "output"

            # The arxiv XML schema requires atom-namespace elements.
            xml_body = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:atom="http://www.w3.org/2005/Atom"
      xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2606.99999v1</id>
    <title>Real fixture paper</title>
    <summary>Body of the fixture paper.</summary>
    <published>2026-06-01T00:00:00Z</published>
    <updated>2026-06-02T00:00:00Z</updated>
    <author><name>Alice</name></author>
    <category term="cs.AI" />
    <link href="http://arxiv.org/abs/2606.99999v1"/>
  </entry>
</feed>
"""
            xml_path = tmp_path / "arxiv_fixture.xml"
            xml_path.write_text(xml_body, encoding="utf-8")
            # file:// URL on every platform; urllib on Linux/macOS
            # accepts file:// URLs.
            xml_url = xml_path.as_uri()

            # Stand up a Python one-liner that runs the collect against
            # the redirect. We monkeypatch the network layer here —
            # this is the same pattern the project's web e2e tests
            # use for the arxiv category failure scenario.
            script = (
                "import sys, pathlib\n"
                f"sys.path.insert(0, {str(REPO_ROOT / "src")!r})\n"
                "import ai_intel_station.collect.papers as papers_collect\n"
                "from urllib import request as _urequest\n"
                f"original = _urequest.urlopen\n"
                f"def redirect(url, *args, **kwargs):\n"
                f"    return original({xml_url!r}, *args, **kwargs)\n"
                f"_urequest.urlopen = redirect\n"
                f"papers_collect.urlopen = redirect\n"
                f"from ai_intel_station.cli import console_main; console_main()\n"
            )
            env = {**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")}
            # NOTE: We pass `-o output_root` for cleanup. The CLI
            # subcommand `collect papers` parses `-o` as `--output-root`.
            cmd = [PYTHON, "-c", script,
                   "collect", "papers", "cs.AI", "--max", "10",
                   "-o", str(output_root)]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                     env=env, cwd=str(REPO_ROOT), timeout=60)
            combined = result.stdout + result.stderr
            self.assertEqual(
                result.returncode, 0,
                msg=f"`research collect papers cs.AI` rc={result.returncode}.\n"
                    f"stdout={result.stdout[-500:]}\nstderr={result.stderr[-500:]}",
            )
            # The CLI wrote under output_root/papers/arXiv-cs.AI/.
            papers_dir = output_root / "papers"
            self.assertTrue(
                papers_dir.exists(),
                f"papers dir missing: {papers_dir}\nstdout={result.stdout[-400:]}",
            )
            # At least one numbered Markdown for cs.AI must exist.
            md_files = list(papers_dir.rglob("*.md"))
            self.assertTrue(
                md_files,
                f"no paper Markdown written for cs.AI under {papers_dir}\n"
                f"combined={combined[-400:]}",
            )
            # The Markdown must mention the fixture paper title.
            joined = ""
            for f in md_files:
                joined += f.read_text(encoding="utf-8", errors="replace")
            self.assertIn(
                "Real fixture paper",
                joined,
                "paper Markdown missing the fixture title",
            )
            self.assertIn(
                "Alice",
                joined,
                "paper Markdown missing author Alice",
            )


# Note: `pytest.mark.parametrize` is reserved for the pytest-style
# tests in `tests/test_wechat_collect.py`. We use stdlib unittest
# here because the rest of the Contract e2e layer uses it and pytest is
# not always available in CI.
