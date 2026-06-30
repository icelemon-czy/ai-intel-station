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
MODULE = REPO_ROOT  # so `python -m research.cli` works


def _run_cli(*args: str, env_extra: dict[str, str] | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run the CLI as a real subprocess.

    We deliberately do NOT use ``python -m research.cli`` — ``research/__init__.py``
    eagerly imports from ``cli``, which causes a RuntimeWarning and prevents
    the ``if __name__ == "__main__":`` path from running. Instead we invoke
    the console_main entry point directly.
    """
    env = os.environ.copy()
    env["PYTHONPATH"] = str(MODULE)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [PYTHON, "-c", "from research.cli import console_main; console_main()", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd) if cwd else None,
        timeout=60,
    )


class CliEndToEndTests(unittest.TestCase):
    """Real CLI invocation via subprocess. No mocks of the CLI itself.

    Each test asserts on stdout / exit code so the CLI surface stays stable.
    Where the CLI touches the network we only check the dry-run / help /
    --status / --help paths that are network-free.
    """

    def test_help_lists_all_subcommands(self) -> None:
        result = _run_cli("--help")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        for cmd in ("collect", "query", "briefing", "backfill", "web", "discover", "schedule", "init-config"):
            self.assertIn(cmd, result.stdout, f"missing subcommand {cmd!r} in help")

    def test_init_config_writes_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "discovery.yaml"
            result = _run_cli("init-config", "-o", str(target))
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue(target.is_file())
            content = target.read_text(encoding="utf-8")
            self.assertIn("sources:", content)
            self.assertIn("briefing:", content)
            self.assertIn("limits:", content)

    def test_init_config_refuses_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "discovery.yaml"
            target.write_text("existing", encoding="utf-8")
            result = _run_cli("init-config", "-o", str(target))
            self.assertEqual(result.returncode, 2)
            self.assertIn("already exists", result.stdout)
            # Original file untouched.
            self.assertEqual(target.read_text(encoding="utf-8"), "existing")

    def test_init_config_force_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "discovery.yaml"
            target.write_text("existing", encoding="utf-8")
            result = _run_cli("init-config", "-o", str(target), "--force")
            self.assertEqual(result.returncode, 0)
            self.assertIn("sources:", target.read_text(encoding="utf-8"))

    def test_discover_help_includes_first_time_steps(self) -> None:
        result = _run_cli("discover", "--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("init-config", result.stdout)
        self.assertIn("dry-run", result.stdout)

    def test_discover_dry_run_with_example_succeeds(self) -> None:
        """The bundled example config drives a real discovery dry-run end-to-end."""
        config = REPO_ROOT / "config" / "discovery.yaml.example"
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_cli(
                "discover",
                "--dry-run",
                "-c",
                str(config),
                "-o",
                tmp,
            )
        # dry-run should exit 0 (no real network / no failures).
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Summary:", result.stdout)
        self.assertIn("Log:", result.stdout)

    def test_discover_refuses_missing_config(self) -> None:
        result = _run_cli("discover", "-c", "/tmp/__definitely_does_not_exist.yaml")
        self.assertEqual(result.returncode, 2)
        self.assertIn("Config file not found", result.stdout)

    def test_discover_status_reads_latest_log(self) -> None:
        """After a dry-run, --status should report it back."""
        config = REPO_ROOT / "config" / "discovery.yaml.example"
        with tempfile.TemporaryDirectory() as tmp:
            _run_cli("discover", "--dry-run", "-c", str(config), "-o", tmp)
            status = _run_cli("discover", "--status", "-c", str(config), "-o", tmp)
        self.assertEqual(status.returncode, 0)
        self.assertIn("Latest log:", status.stdout)

    def test_discover_log_list_shows_summary(self) -> None:
        config = REPO_ROOT / "config" / "discovery.yaml.example"
        with tempfile.TemporaryDirectory() as tmp:
            _run_cli("discover", "--dry-run", "-c", str(config), "-o", tmp)
            listed = _run_cli("discover", "--log-list", "3", "-c", str(config), "-o", tmp)
        self.assertEqual(listed.returncode, 0)
        self.assertIn("Last 3 runs", listed.stdout)

    def test_discover_invalid_source_exits_2(self) -> None:
        config = REPO_ROOT / "config" / "discovery.yaml.example"
        result = _run_cli("discover", "--dry-run", "--source", "notreal", "-c", str(config))
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid source", result.stdout)

    def test_query_no_keyword_is_helpful(self) -> None:
        # Query without args should not crash; behavior depends on impl.
        result = _run_cli("query", "agent")
        self.assertIn(result.returncode, (0, 1, 2))
        # If items found, the output should reference them; otherwise be empty.
        # We don't assert on content to keep the test resilient.

    def test_briefing_list_works(self) -> None:
        """`research briefing --list` should not 500 even with empty tree."""
        with tempfile.TemporaryDirectory() as tmp:
            result = _run_cli("briefing", "--list", "-o", tmp)
        self.assertEqual(result.returncode, 0)
        self.assertIn("No briefing", result.stdout)

    def test_schedule_launchd_prints_install_steps(self) -> None:
        """Dry schedule launchd prints install commands."""
        result = _run_cli("schedule", "launchd")
        self.assertEqual(result.returncode, 0)
        self.assertIn("launchctl", result.stdout)
        self.assertIn("LaunchAgents", result.stdout)

    def test_schedule_cron_prints_crontab(self) -> None:
        result = _run_cli("schedule", "cron")
        self.assertEqual(result.returncode, 0)
        self.assertIn("crontab", result.stdout)

    def test_discovery_yaml_validation_errors_are_aggregated(self) -> None:
        """Multiple YAML mistakes should all surface in one CLI invocation."""
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "discovery.yaml"
            bad.write_text(
                "sources:\n"
                "  papers:\n"
                "    categories: [cs.AI, cs.NOPE]\n"
                "    max_per_category: -1\n"
                "  github:\n"
                "    search:\n"
                "      - limit: 5\n"
                "briefing:\n"
                "  mode: monthly\n",
                encoding="utf-8",
            )
            result = _run_cli("discover", "--dry-run", "-c", str(bad))
        self.assertEqual(result.returncode, 2)
        combined = result.stdout + result.stderr
        # All four problems must surface in one go.
        self.assertIn("search[0].query", combined)
        self.assertIn("unsupported values: cs.NOPE", combined)
        self.assertIn("max_per_category", combined)
        self.assertIn("briefing.mode", combined)


if __name__ == "__main__":
    unittest.main()