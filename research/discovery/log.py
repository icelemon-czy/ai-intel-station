from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


class DiscoveryLogger:
    """Dual stdout + file logger that survives crashes mid-run.

    Writes to ``<log_dir>/<YYYY-MM-DDTHH-MM-SS>.log``; tee'd to terminal.
    When the directory holds more than ``max_log_files`` files, the oldest
    are pruned on each new run to keep the log directory bounded.
    """

    DEFAULT_MAX_LOG_FILES = 30

    def __init__(self, log_dir: Path, *, max_log_files: int = DEFAULT_MAX_LOG_FILES) -> None:
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_log_files = max(0, int(max_log_files))
        if self.max_log_files > 0:
            self._prune_old_logs()
        stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%dT%H-%M-%S")
        self.path = self.log_dir / f"{stamp}.log"
        self._handle = self.path.open("a", encoding="utf-8")
        self._start = datetime.now()

    def _prune_old_logs(self) -> None:
        """Delete oldest ``*.log`` files so the directory has at most
        ``max_log_files - 1`` entries (the current run will become the Nth).
        """
        existing = sorted(
            self.log_dir.glob("*.log"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # Keep the newest max_log_files-1; the new run will become the Nth.
        keep = max(0, self.max_log_files - 1)
        for stale in existing[keep:]:
            try:
                stale.unlink()
            except OSError:
                # Best-effort cleanup; never let log rotation break a run.
                pass

    def close(self) -> None:
        if self._handle.closed:
            return
        elapsed = (datetime.now() - self._start).total_seconds()
        try:
            self._handle.write(f"\n=== finished in {elapsed:.1f}s ===\n")
            self._handle.flush()
        except OSError:
            # Disk full / unlinked file. Fall through and try to close
            # anyway — better than crashing the caller.
            pass
        try:
            self._handle.close()
        except OSError:
            pass

    def __enter__(self) -> "DiscoveryLogger":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            # Even when the handle was already closed we still want a
            # best-effort attempt to log the error so a downstream
            # post-mortem can find it. Use stderr as the always-on
            # fallback so 'log()' silent-return when the handle is
            # closed does not eat the real cause.
            message = f"ERROR: {exc_type.__name__}: {exc}"
            if not self._handle.closed:
                try:
                    self._handle.write(f"{message}\n")
                    self._handle.flush()
                except OSError:
                    pass
            else:
                print(message)
        self.close()

    def log(self, message: str) -> None:
        if self._handle.closed:
            print(message)
            return
        try:
            self._handle.write(f"{message}\n")
            self._handle.flush()
        except OSError:
            print(message)
        print(message)

    def header(self, title: str) -> None:
        self.log("")
        self.log(f"=== {title} ===")


def recent_log_paths(log_dir: Path, limit: int = 5) -> list[Path]:
    """Return the up-to-``limit`` most recent ``.log`` files under ``log_dir``,
    newest first. Returns ``[]`` when the directory is missing or empty."""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return []
    candidates = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[: max(0, limit)]


def latest_log_path(log_dir: Path) -> Path | None:
    """Return the path of the most recent ``.log`` file under ``log_dir``, or
    ``None`` when no log files exist yet."""
    log_dir = Path(log_dir)
    if not log_dir.exists():
        return None
    candidates = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def read_log_summary(path: Path) -> dict:
    """Extract the most recent run summary from a discovery log file.

    The log is line-oriented text; we look for the ``Summary:`` and
    ``Briefing:`` lines emitted by :func:`run_discovery`. Missing fields fall
    back to ``None`` rather than raising so callers can show "no run yet".
    """
    path = Path(path)
    if not path.is_file():
        return {"path": path, "exists": False, "summary": None, "briefing": None, "started_at": None, "finished_at": None}

    text = path.read_text(encoding="utf-8", errors="replace")
    summary: dict = {
        "path": path,
        "exists": True,
        "summary": None,
        "briefing": None,
        "started_at": None,
        "finished_at": None,
    }

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("📊 Summary:"):
            summary["summary"] = line.removeprefix("📊 Summary:").strip()
        elif line.startswith("📰 Briefing:"):
            summary["briefing"] = line.removeprefix("📰 Briefing:").strip()
        elif line.startswith('"started_at":'):
            summary["started_at"] = line.split(":", 1)[1].strip().rstrip(",").strip('"')
        elif line.startswith('"finished_at":'):
            summary["finished_at"] = line.split(":", 1)[1].strip().rstrip(",").strip('"')

    return summary