from __future__ import annotations

import copy
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path


MAX_JOBS = 32
_JOBS: dict[str, dict] = {}
_JOBS_LOCK = threading.Lock()


def _resolve_discovery_log_dir() -> Path:
    from ai_intel_station.discovery.config import DEFAULT_CONFIG_PATH, DEFAULT_LOG_DIR

    if not DEFAULT_CONFIG_PATH.exists():
        return DEFAULT_LOG_DIR
    try:
        from ai_intel_station.discovery import load_config

        return load_config(DEFAULT_CONFIG_PATH).log_dir
    except Exception:  # invalid config must not break the read-only status page
        return DEFAULT_LOG_DIR


def run_discover_from_request(output_root: Path, payload: dict) -> dict:
    from ai_intel_station.discovery import (
        DEFAULT_CONFIG_PATH,
        DiscoveryConfigError,
        load_config,
        run_discovery,
    )

    config_path = Path(payload.get("config_path") or DEFAULT_CONFIG_PATH)
    try:
        config = load_config(config_path)
    except DiscoveryConfigError as exc:
        return {"status": "config_error", "message": str(exc), "config_path": str(config_path)}
    # The Web workspace's archive root is part of the server boundary.  A
    # checked-in/default discovery config must never redirect a test server or
    # an explicitly configured Web instance back to the repository archive.
    config.output_root = output_root.resolve()
    report = run_discovery(
        config,
        only=payload.get("only") or None,
        dry_run=bool(payload.get("dry_run", False)),
        enable_briefing=not bool(payload.get("no_briefing", False)),
        log_dir=config.log_dir,
    )
    result = report.to_dict()
    result["status"] = (
        "partial" if any(source.get("failed") for source in result["sources"].values()) else "ok"
    )
    return result


def _evict_old_jobs() -> None:
    if len(_JOBS) <= MAX_JOBS:
        return
    finished = sorted(
        (
            (job_id, record)
            for job_id, record in _JOBS.items()
            if record.get("status") != "running"
        ),
        key=lambda item: item[1].get("started_at", ""),
    )
    for job_id, _ in finished[: len(_JOBS) - MAX_JOBS]:
        _JOBS.pop(job_id, None)


def start_discover_job(output_root: Path, payload: dict) -> dict:
    job_id = uuid.uuid4().hex[:12]
    with _JOBS_LOCK:
        _JOBS[job_id] = {
            "status": "running",
            "result": None,
            "started_at": datetime.now().isoformat(timespec="seconds"),
        }
        _evict_old_jobs()

    def _run() -> None:
        try:
            result = run_discover_from_request(output_root, payload)
        except Exception as exc:  # keep thread failure inside the job contract
            result = {"status": "error", "message": str(exc)}
        snapshot = copy.deepcopy(result) if isinstance(result, dict) else {
            "status": "error",
            "message": str(result),
        }
        with _JOBS_LOCK:
            _JOBS[job_id]["result"] = snapshot
            _JOBS[job_id]["status"] = snapshot.get("status", "error")
            _JOBS[job_id]["finished_at"] = datetime.now().isoformat(timespec="seconds")

    threading.Thread(target=_run, name=f"discover-{job_id}", daemon=True).start()
    return {"job_id": job_id, "status": "running"}


def get_job(job_id: str) -> dict | None:
    with _JOBS_LOCK:
        record = _JOBS.get(job_id)
        return copy.deepcopy(record) if record else None


_BRIEFING_RE = re.compile(
    r"^(?P<path>\S+)\s*\((?P<count>\d+)\s+items?"
    r"(?:,\s*status=(?P<status>ready|partial|no_fresh_signals|coverage_incomplete|failed|dry_run|legacy))?\)$"
)


def _parse_briefing_marker(text: str | None) -> dict | None:
    if not text or not (match := _BRIEFING_RE.match(text.strip())):
        return None
    path = match.group("path")
    if path.startswith("output/"):
        path = path[len("output/") :]
    result = {"path": None if path == "None" else path, "item_count": int(match.group("count"))}
    if match.group("status"):
        result["status"] = match.group("status")
    return result


def discover_status_payload(output_root: Path) -> dict:
    from ai_intel_station.discovery import latest_log_path, read_log_summary

    log_dir = _resolve_discovery_log_dir()
    path = latest_log_path(log_dir)
    if path is None:
        return {"has_run": False, "log_dir": str(log_dir)}
    info = read_log_summary(path)
    briefing = _parse_briefing_marker(info["briefing"])
    if briefing is not None and info.get("briefing_status") and "status" not in briefing:
        briefing["status"] = info["briefing_status"]
    return {
        "has_run": True,
        "log_path": info["path"].as_posix(),
        "started_at": info["started_at"],
        "finished_at": info["finished_at"],
        "summary": info["summary"],
        "briefing_status": info.get("briefing_status"),
        "briefing": briefing,
    }
