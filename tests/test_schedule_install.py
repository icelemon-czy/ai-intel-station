from __future__ import annotations

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from research.discovery.scripts import (
    install_cron,
    install_launchd,
    render_install_instructions,
)


@contextmanager
def _tempdir():
    cm = tempfile.TemporaryDirectory()
    try:
        yield cm.name
    finally:
        cm.cleanup()


class _FakeProc:
    def __init__(self, stdout: str = "", stderr: str = "", returncode: int = 0) -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _make_runner(log: list[list[str]]):
    """A runner stub that records every command and returns a success fake."""

    def runner(command, **kwargs):
        log.append(list(command))
        # cron "crontab -" reads from stdin (kwargs["input"]); we accept it.
        if kwargs.get("input"):
            log[-1].append(f"<input {len(kwargs['input'])} chars>")
        return _FakeProc(returncode=0, stdout=f"ran: {' '.join(command)}")

    return runner


class ScheduleInstallTests(unittest.TestCase):
    """Real install_* paths — no real ``launchctl`` / ``crontab`` is invoked
    because we inject a fake runner. We do write the plist / backup to a
    sandbox directory and verify the on-disk artifacts."""

    def test_install_launchd_writes_plist_to_home(self) -> None:
        with unittest.TestCase()._tempdir() if False else _tempdir() as tmp:
            fake_home = Path(tmp) / "home"
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            (repo_root / "config").mkdir()
            runner_log: list[list[str]] = []

            plist_path, output = install_launchd(
                repo_root,
                home_dir=fake_home,
                runner=_make_runner(runner_log),
            )

            # Plist exists, points to repo's absolute path.
            self.assertTrue(plist_path.is_file())
            plist_text = plist_path.read_text(encoding="utf-8")
            self.assertIn(str(repo_root.as_posix()), plist_text)
            self.assertIn("com.ai-intel-station.daily", plist_text)
            self.assertIn("Label</key>", plist_text)

            # Exactly one subprocess call, the launchctl load.
            self.assertEqual(len(runner_log), 1)
            self.assertEqual(runner_log[0][0], "launchctl")
            self.assertEqual(runner_log[0][1], "load")
            self.assertEqual(runner_log[0][2], "-w")
            self.assertEqual(runner_log[0][3], str(plist_path))

            # Output captured.
            self.assertIn("ran: launchctl load", output)

    def test_install_launchd_uses_resolved_uv_path(self) -> None:
        """The plist should reference *a* uv binary, either resolved or the venv fallback."""
        with _tempdir() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            plist_path, _ = install_launchd(
                repo_root,
                home_dir=Path(tmp) / "home",
                runner=_make_runner([]),
            )
            plist_text = plist_path.read_text(encoding="utf-8")
            # Either `which uv` found something or we fell back to .venv/bin/uv.
            self.assertTrue(
                "uv" in plist_text,
                f"expected 'uv' in plist, got:\n{plist_text}",
            )

    def test_install_cron_merges_existing_crontab(self) -> None:
        with _tempdir() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            backup = Path(tmp) / "crontab.bak"
            existing = "0 5 * * *  /usr/local/bin/cleanup\n"

            def runner(command, **kwargs):
                if command == ["crontab", "-l"]:
                    return _FakeProc(stdout=existing, returncode=0)
                # crontab - receives stdin (kwargs["input"]); capture for assertion.
                if command == ["crontab", "-"]:
                    self.captured_input = kwargs.get("input", "")
                    return _FakeProc(returncode=0, stdout=f"ran: {' '.join(command)}")
                return _FakeProc(returncode=0)

            output, returned_backup = install_cron(
                repo_root,
                backup_path=backup,
                runner=runner,
            )

            # Backup was written with the previous contents.
            self.assertEqual(backup.read_text(encoding="utf-8"), existing)
            self.assertEqual(returned_backup, str(backup))

            # The captured input merges the existing crontab with our new block.
            self.assertIn("/usr/local/bin/cleanup", self.captured_input)
            self.assertIn("research discover", self.captured_input)
            # Our new entry goes AFTER the existing one.
            cleanup_pos = self.captured_input.find("/usr/local/bin/cleanup")
            research_pos = self.captured_input.find("research discover")
            self.assertLess(cleanup_pos, research_pos)
            self.assertIn("ran: crontab -", output)

    def test_install_cron_handles_no_existing_crontab(self) -> None:
        with _tempdir() as tmp:
            repo_root = Path(tmp) / "repo"
            repo_root.mkdir()
            backup = Path(tmp) / "crontab.bak"

            def runner(command, **kwargs):
                if command == ["crontab", "-l"]:
                    return _FakeProc(stdout="", returncode=1, stderr="no crontab")
                if command == ["crontab", "-"]:
                    self.captured_input = kwargs.get("input", "")
                    return _FakeProc(returncode=0)
                return _FakeProc(returncode=0)

            _, returned_backup = install_cron(
                repo_root,
                backup_path=backup,
                runner=runner,
            )

            # No existing crontab → no backup file should be written.
            self.assertFalse(backup.exists())
            self.assertEqual(returned_backup, str(backup))
            self.assertIn("research discover", self.captured_input)


class ScheduleRenderTests(unittest.TestCase):
    def test_render_install_instructions_launchd_has_install_command(self) -> None:
        with _tempdir() as tmp:
            text = render_install_instructions("launchd", Path(tmp))
        self.assertIn("cp ", text)
        self.assertIn("launchctl load", text)
        self.assertIn("LaunchAgents", text)
        self.assertIn(".state/discovery/", text)
        self.assertNotIn(".ai/", text)

    def test_render_install_instructions_cron_has_crontab(self) -> None:
        with _tempdir() as tmp:
            text = render_install_instructions("cron", Path(tmp))
        self.assertIn("crontab", text)
        self.assertIn(str(Path(tmp).as_posix()), text)
        self.assertIn(".state/discovery/cron.log", text)
        self.assertNotIn(".ai/", text)


import tempfile as _tempfile


if __name__ == "__main__":
    unittest.main()
