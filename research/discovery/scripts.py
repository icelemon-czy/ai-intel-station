from __future__ import annotations

import platform as _platform_mod
import shutil
from pathlib import Path
from textwrap import dedent


LAUNCHD_LABEL = "com.ai-intel-station.daily"
LAUNCHD_TEMPLATE_NAME = f"{LAUNCHD_LABEL}.plist"


def _render_launchd(repo_root: Path) -> str:
    """Render the launchd plist with the absolute paths to this repo."""
    uv_path = shutil.which("uv") or str(repo_root / ".venv" / "bin" / "uv")
    return dedent(
        f"""\
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>{LAUNCHD_LABEL}</string>
            <key>ProgramArguments</key>
            <array>
                <string>{uv_path}</string>
                <string>run</string>
                <string>research</string>
                <string>discover</string>
            </array>
            <key>WorkingDirectory</key>
            <string>{repo_root.as_posix()}</string>
            <key>StartCalendarInterval</key>
            <dict>
                <key>Hour</key>
                <integer>9</integer>
                <key>Minute</key>
                <integer>0</integer>
            </dict>
            <key>StandardOutPath</key>
            <string>/tmp/ai-intel-station.daily.out</string>
            <key>StandardErrorPath</key>
            <string>/tmp/ai-intel-station.daily.err</string>
            <key>RunAtLoad</key>
            <false/>
        </dict>
        </plist>
        """
    )


def _render_cron(repo_root: Path) -> str:
    return dedent(
        f"""\
        # AI Intel Station — daily discovery at 09:07 local time.
        # Pick an off-minute to avoid the :00 cron stampede.
        7 9 * * *  cd {repo_root.as_posix()} && mkdir -p .state/discovery && uv run research discover >> .state/discovery/cron.log 2>&1
        """
    )


def render_install_instructions(platform: str, repo_root: Path) -> str:
    repo_root = Path(repo_root)
    if platform == "launchd":
        plist_src = repo_root / "scripts" / "launchd" / LAUNCHD_TEMPLATE_NAME
        plist_dst = Path.home() / "Library" / "LaunchAgents" / LAUNCHD_TEMPLATE_NAME
        steps = [
            f"# macOS launchd install (9:00 AM every day)",
            f"mkdir -p {plist_dst.parent}",
            f"cp {plist_src} {plist_dst}",
            f"launchctl load -w {plist_dst}",
            "",
            "# Check status / unload:",
            f"launchctl list | grep {LAUNCHD_LABEL}",
            f"launchctl unload {plist_dst}",
            "",
            "# Logs:",
            "tail -f /tmp/ai-intel-station.daily.out",
            f"tail -f {repo_root.as_posix()}/.state/discovery/*.log",
            "",
            "# rendered plist content:",
            _render_launchd(repo_root),
        ]
        return "\n".join(steps)

    if platform == "cron":
        return "\n".join(
            [
                "# crontab install (Linux + macOS fallback)",
                f"crontab -l > /tmp/ais-cron.bak 2>/dev/null || true",
                f"( crontab -l 2>/dev/null; cat <<'EOF'",
                _render_cron(repo_root).rstrip(),
                "EOF",
                ") | crontab -",
                "",
                "# Verify:",
                "crontab -l | grep ai-intel-station",
            ]
        )

    raise ValueError(f"Unknown platform: {platform!r}")


def install_launchd(
    repo_root: Path,
    *,
    home_dir: Path | None = None,
    runner=None,
) -> tuple[Path, str]:
    """Render the launchd plist at the user's LaunchAgents dir and load it.

    Returns ``(plist_path, launchctl_output)``.

    Parameters
    ----------
    home_dir:
        Override ``Path.home()`` for testing. Defaults to the real home.
    runner:
        Optional callable accepting ``(command, **kwargs)`` and returning a
        ``CompletedProcess``-like object. Defaults to ``subprocess.run``.
    """
    import subprocess

    repo_root = Path(repo_root)
    home = home_dir or Path.home()
    plist_dst = home / "Library" / "LaunchAgents" / LAUNCHD_TEMPLATE_NAME
    plist_dst.parent.mkdir(parents=True, exist_ok=True)
    plist_dst.write_text(_render_launchd(repo_root), encoding="utf-8")
    run = runner or subprocess.run
    completed = run(
        ["launchctl", "load", "-w", str(plist_dst)],
        capture_output=True,
        text=True,
    )
    output = (completed.stdout + completed.stderr).strip()
    return plist_dst, output


def install_cron(
    repo_root: Path,
    *,
    backup_path: Path | None = None,
    runner=None,
) -> tuple[str, str]:
    """Install the cron entry non-interactively. Returns ``(crontab_output, backup_path)``.

    Parameters
    ----------
    backup_path:
        Override ``/tmp/ais-cron.bak`` for testing.
    runner:
        Optional callable accepting ``(command, **kwargs)`` and returning a
        ``CompletedProcess``-like object.
    """
    import subprocess

    repo_root = Path(repo_root)
    backup = Path(backup_path) if backup_path else Path("/tmp/ais-cron.bak")
    run = runner or subprocess.run
    existing = ""
    listed = run(["crontab", "-l"], capture_output=True, text=True)
    if listed.returncode == 0:
        existing = listed.stdout
        backup.parent.mkdir(parents=True, exist_ok=True)
        backup.write_text(existing, encoding="utf-8")
    new_block = _render_cron(repo_root)
    merged = existing.rstrip("\n") + "\n" + new_block
    piped = run(
        ["crontab", "-"],
        input=merged,
        capture_output=True,
        text=True,
    )
    return (piped.stdout + piped.stderr).strip(), str(backup)


def installed_platform() -> str:
    if _platform_mod.system() == "Darwin":
        return "launchd"
    return "cron"
