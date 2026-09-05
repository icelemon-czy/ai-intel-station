"""Regression tests for ``research.discovery.config.load_config`` IO
errors.

The previous version used ``config_path.exists()`` which only catches
FileNotFoundError. A path that exists but is a directory (or a
symlink to a deleted target) would raise IsADirectoryError /
PermissionError uncaught. We now use ``is_file()`` and a defensive
OSError catch.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research.discovery.config import DiscoveryConfigError, load_config


class LoadConfigIOTests(unittest.TestCase):
    def test_missing_file_raises_friendly_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "absent.yaml"
            with self.assertRaises(DiscoveryConfigError) as ctx:
                load_config(missing)
            self.assertIn("not found", str(ctx.exception).lower())
            self.assertIn(str(missing), str(ctx.exception))

    def test_directory_instead_of_file_raises_friendly_error(self) -> None:
        # A directory is not a file. The old code used ``exists()``
        # which would say True here; ``read_text`` would then raise
        # IsADirectoryError uncaught.
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / "config"
            directory.mkdir()
            with self.assertRaises(DiscoveryConfigError) as ctx:
                load_config(directory)
            self.assertIn(str(directory), str(ctx.exception))

    def test_string_path_argument_works(self) -> None:
        # Callers may pass a string instead of a Path; both must work.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "discovery.yaml"
            path.write_text(
                "output_root: output\n"
                "log_dir: .state/discovery\n"
                "sources: {}\n"
                "briefing: {enabled: false}\n"
                "limits: {}\n",
                encoding="utf-8",
            )
            cfg = load_config(str(path))
            self.assertEqual(cfg.output_root.name, "output")


if __name__ == "__main__":
    unittest.main()
