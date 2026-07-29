from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from research.cli import run_discover, run_init_config
from research.discovery import DEFAULT_CONFIG_PATH, render_example_config


class DiscoverCliTests(unittest.TestCase):
    def test_discover_refuses_without_config(self) -> None:
        """First-time users without config should NOT silently run with example.

        Uses a clearly-missing path that is NOT ``DEFAULT_CONFIG_PATH`` to
        exercise the load_config error path (returns 2 with a clear message).
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fake_config = tmp_path / "discovery.yaml"  # does not exist
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_discover(
                    fake_config,
                    only=None,
                    dry_run=False,
                    output_root=tmp_path / "output",
                )
            self.assertEqual(exit_code, 2)
            output = buf.getvalue()
            self.assertIn("Config file not found", output)

    def test_discover_dry_run_with_real_example_succeeds(self) -> None:
        """When the example config exists, dry-run with it succeeds (no network)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_discover(
                    DEFAULT_CONFIG_PATH,  # missing on purpose
                    only=None,
                    dry_run=True,
                    output_root=tmp_path / "output",
                )
            # 0 = clean run, or 1 = some sources reported skipped/failed but ran.
            self.assertIn(exit_code, (0, 1))
            output = buf.getvalue()
            self.assertIn("using", output)


class InitConfigCliTests(unittest.TestCase):
    def test_init_config_writes_file_and_prints_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "discovery.yaml"
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_init_config(target=target)
            self.assertEqual(exit_code, 0)
            self.assertTrue(target.is_file())
            content = target.read_text(encoding="utf-8")
            self.assertEqual(content, render_example_config())

            output = buf.getvalue()
            # The new "Next steps" block.
            self.assertIn("Next steps:", output)
            self.assertIn("--dry-run", output)
            self.assertIn("schedule launchd --install", output)

    def test_init_config_refuses_to_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "discovery.yaml"
            target.write_text("existing", encoding="utf-8")
            buf = io.StringIO()
            with redirect_stdout(buf):
                exit_code = run_init_config(target=target)
            self.assertEqual(exit_code, 2)
            self.assertIn("already exists", buf.getvalue())
            # File was NOT overwritten.
            self.assertEqual(target.read_text(encoding="utf-8"), "existing")

    def test_discover_help_includes_first_time_steps(self) -> None:
        """`research discover --help` must guide first-time users."""
        repo_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(repo_root)
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from research.cli import console_main; console_main()",
                "discover",
                "--help",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        self.assertEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("init-config", combined)
        self.assertIn("dry-run", combined)
        self.assertIn("First time", combined)


if __name__ == "__main__":
    unittest.main()
