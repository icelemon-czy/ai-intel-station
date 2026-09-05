from __future__ import annotations

import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from ai_intel_station.cli.commands import run_discover_status
from ai_intel_station.discovery import load_config, render_example_config, run_discovery
from ai_intel_station.discovery.scripts import _render_cron
from ai_intel_station.adapters.web.service import run_discover_from_request


MINIMAL_CONFIG = """\
output_root: {output_root}
{log_dir}
sources:
  github:
    enabled: false
  papers:
    enabled: false
  wechat:
    enabled: false
briefing:
  enabled: false
limits:
  max_log_files: 30
"""


class DiscoveryStateMigrationTests(unittest.TestCase):
    def test_default_run_status_and_log_list_share_new_directory(self) -> None:
        from ai_intel_station.discovery import config as config_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            default_log_dir = root / ".state" / "discovery"
            config_path = root / "discovery.yaml"
            config_path.write_text(
                MINIMAL_CONFIG.format(output_root=root / "output", log_dir=""),
                encoding="utf-8",
            )
            original_default = config_module.DEFAULT_LOG_DIR
            config_module.DEFAULT_LOG_DIR = default_log_dir
            try:
                config = load_config(config_path)
                report = run_discovery(config, dry_run=True, enable_briefing=False)
                self.assertTrue(report.dry_run)
                self.assertTrue(list(default_log_dir.glob("*.log")))

                stdout = io.StringIO()
                with contextlib.redirect_stdout(stdout):
                    self.assertEqual(run_discover_status(config_path, last=1), 0)
                    self.assertEqual(run_discover_status(config_path, last=3), 0)
            finally:
                config_module.DEFAULT_LOG_DIR = original_default

        output = stdout.getvalue()
        self.assertIn("Latest log:", output)
        self.assertIn("Last 1 runs", output)

    def test_legacy_explicit_directory_keeps_existing_sentinel(self) -> None:
        from ai_intel_station.discovery import config as config_module

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            legacy_dir = root / ".ai" / "L4-session" / "discovery"
            legacy_dir.mkdir(parents=True)
            sentinel = legacy_dir / "20000101T000000.log"
            sentinel.write_text("legacy sentinel\n", encoding="utf-8")
            before = sentinel.stat().st_mtime_ns
            config_path = root / "discovery.yaml"
            config_path.write_text(
                MINIMAL_CONFIG.format(
                    output_root=root / "output",
                    log_dir="log_dir: .ai/L4-session/discovery",
                ),
                encoding="utf-8",
            )

            original_root = config_module.REPO_ROOT
            config_module.REPO_ROOT = root
            try:
                config = load_config(config_path)
                self.assertEqual(config.log_dir, legacy_dir)
                run_discovery(config, dry_run=True, enable_briefing=False)
            finally:
                config_module.REPO_ROOT = original_root

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "legacy sentinel\n")
            self.assertEqual(sentinel.stat().st_mtime_ns, before)

    def test_generated_cron_bootstraps_state_directory_before_uv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_uv = fake_bin / "uv"
            fake_uv.write_text(
                "#!/bin/sh\nprintf 'called' > uv-called\n",
                encoding="utf-8",
            )
            fake_uv.chmod(0o755)

            cron_line = [
                line for line in _render_cron(root).splitlines()
                if line and not line.startswith("#")
            ][0]
            command = cron_line.split("  ", 1)[1]
            result = subprocess.run(
                ["/bin/sh", "-c", command],
                capture_output=True,
                text=True,
                env={"PATH": f"{fake_bin}:/usr/bin:/bin"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "uv-called").read_text(encoding="utf-8"), "called")
            self.assertTrue((root / ".state" / "discovery" / "cron.log").is_file())

    def test_web_run_uses_payload_config_log_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            custom_log_dir = root / "custom-logs"
            config_path = root / "discovery.yaml"
            config_path.write_text(
                MINIMAL_CONFIG.format(
                    output_root=root / "output",
                    log_dir=f"log_dir: {custom_log_dir}",
                ),
                encoding="utf-8",
            )

            result = run_discover_from_request(
                root / "output",
                {
                    "config_path": str(config_path),
                    "dry_run": True,
                    "no_briefing": True,
                },
            )

            self.assertEqual(result["status"], "ok")
            self.assertTrue(list(custom_log_dir.glob("*.log")))

    def test_examples_and_ignore_boundaries_stay_synchronized(self) -> None:
        from ai_intel_station.discovery import EXAMPLE_CONFIG_PATH

        repo_root = Path(__file__).resolve().parents[1]
        checked_in = EXAMPLE_CONFIG_PATH.read_text(encoding="utf-8")
        self.assertEqual(render_example_config(), checked_in)
        self.assertIn("log_dir: .state/discovery", checked_in)

        gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".state/", gitignore)
        self.assertIn(".ai/L4-session/discovery/", gitignore)

        cron_example = (
            repo_root
            / "src"
            / "ai_intel_station"
            / "discovery"
            / "schedule"
            / "ai-intel-station.cron.example"
        ).read_text(encoding="utf-8")
        self.assertIn("mkdir -p .state/discovery", cron_example)
        self.assertNotIn(".ai/L4-session/discovery", cron_example)

        web_source = (repo_root / "frontend" / "src" / "DailyDiscoveryCard.jsx").read_text(
            encoding="utf-8"
        )
        built_bundle = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted((repo_root / "src" / "ai_intel_station" / "adapters" / "web" / "static" / "assets").glob("*.js"))
        )
        for text in (web_source, built_bundle):
            self.assertIn(".state/discovery/", text)
            self.assertNotIn(".ai/L4-session/discovery/", text)


if __name__ == "__main__":
    unittest.main()
