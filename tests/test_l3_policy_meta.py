"""Meta-test that locks down the L3 e2e policy at the test-file
level.

`docs/l3-coverage.md` codifies three rules for what counts as a
"real" L3 test. This file encodes those rules as concrete
assertions about which patterns are and aren't allowed in
the L3-tagged test files. If a future contributor reaches for
`monkeypatch.setattr(github_collect, "run_gh", fake)` to write
an L3 test, this meta-test fails before the offending change
lands in CI.

Rules enforced below:

  R1. No `monkeypatch.setattr(<business_module>, ...)` over a
     business function we ship to operators (`collect.github.run_gh`,
     `collect.github.fetch_repo`, `collect.github.save_repo`,
     `collect.papers.fetch_papers_by_category`,
     `collect.papers.save_papers`,
     `collect.wechat.fetch_article`,
     `workspace_web.service.run_collect`,
     `research.cli.run_web_workspace`).
     — replacing any of these with a fake is the very kind of
     mock the L3 spec rules out.

  R2. Network-layer fixtures ARE allowed: a fake `gh` shell
     script on PATH, or a redirected `urllib.request.urlopen`
     pointed at a local file. These don't replace business
     code paths, only the subprocess/HTTP they call.

  R3. `monkeypatch.setattr` is fine when the target is a
     *Python-internal* helper that has no external caller —
     e.g. monkey-patching `time.sleep` for a fast async test.
     That's allowed only in non-L3 unit tests; we don't enforce
     it here because it's a soft rule.

This file itself IS the contract. When the policy is wrong,
update this test *and* the matching section in
`docs/l3-coverage.md`.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


L3_TEST_FILES = [
    Path("tests/test_l3_requirements.py"),
    Path("tests/test_l3_http_e2e.py"),
    Path("tests/test_l3_subspec_e2e.py"),
    Path("tests/test_l3_subspec_remaining_e2e.py"),
    Path("tests/test_e2e_archive.py"),  # contains the L3 classes
]


# Patterns R1 forbids. Each tuple is (regex_pattern, human_label).
FORBIDDEN_BUSINESS_MOCK_PATTERNS = [
    (r"monkeypatch\.setattr\(github_collect,\s*['\"](run_gh|fetch_repo|save_repo)",
     "`monkeypatch` of `collect.github.run_gh`/`fetch_repo`/`save_repo`"),
    (r"monkeypatch\.setattr\(papers_collect,\s*['\"](fetch_papers_by_category|save_papers)",
     "`monkeypatch` of `collect.papers.fetch_papers_by_category`/`save_papers`"),
    (r"monkeypatch\.setattr\(wechat_collect,\s*['\"](fetch_article|normalize_wechat_url)",
     "`monkeypatch` of `collect.wechat.fetch_article`/`normalize_wechat_url`"),
    (r"monkeypatch\.setattr\(['\"]workspace_web\.service['\"],\s*['\"](run_collect)",
     "`monkeypatch` of `workspace_web.service.run_collect`"),
    (r"monkeypatch\.setattr\(['\"]research\.cli['\"],\s*['\"](run_web_workspace)",
     "`monkeypatch` of `research.cli.run_web_workspace`"),
]


class L3NoBusinessMockMetaTest(unittest.TestCase):
    """Scans the L3 test files for any business-layer mock usage.

    Allowable substitutes are *network-layer* fixtures: a fake
    `gh` shell script on PATH, or a redirected `urllib.request.urlopen`
    to a local file. Those don't replace business code; they
    replace the external process that business code calls into.
    """

    def test_each_l3_test_file_has_no_business_layer_mocks(self):
        offenders = []
        for path in L3_TEST_FILES:
            if not path.exists():
                self.fail(f"L3 test file missing: {path}")
            text = path.read_text(encoding="utf-8")
            for pattern, label in FORBIDDEN_BUSINESS_MOCK_PATTERNS:
                for match in re.finditer(pattern, text):
                    # Calculate line number for the diagnostic.
                    line_no = text.count("\n", 0, match.start()) + 1
                    offenders.append(
                        f"  {path}:{line_no}: {label}\n    matching: {match.group(0)!r}"
                    )
        if offenders:
            self.fail(
                "L3 test files must not mock business-layer functions. "
                "See docs/l3-coverage.md for the accepted network-layer "
                "substitutes. Offending lines:\n" + "\n".join(offenders)
            )

    def test_l3_test_files_invoke_real_subprocess_or_real_filesystem(self):
        """Each L3 test file MUST exercise either real subprocess
        boundaries (`subprocess.run`, `ThreadingHTTPServer`,
        `spawn(...)`) or the real local filesystem (seeded
        sidecars via `tmp_path` / `TemporaryDirectory`).
        A pure in-process unit test that never crosses a process
        boundary cannot catch the user-visible L3 contracts."""
        # Heuristic: each L3 file must contain at least one of:
        #   - `subprocess.run` / `subprocess.Popen` / `spawn(`
        #   - `TemporaryDirectory(` / `tmp_path` fixture
        #   - `serve_workspace` (real server bootstrap)
        for path in L3_TEST_FILES:
            text = path.read_text(encoding="utf-8")
            has_subprocess = re.search(r"subprocess\.|spawn\(", text) is not None
            has_filesystem = re.search(
                r"TemporaryDirectory|tmp_path|tempfile|file_path =|fileURL",
                text,
            ) is not None
            has_serve_workspace = "serve_workspace" in text
            ok = has_subprocess or has_filesystem or has_serve_workspace
            self.assertTrue(
                ok,
                f"{path} contains no real-process or real-filesystem "
                f"evidence — an L3 test must cross a real boundary "
                f"(subprocess, real file tree, or real server).",
            )


if __name__ == "__main__":
    unittest.main()
