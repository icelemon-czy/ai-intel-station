from __future__ import annotations

import hashlib
import shutil
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_ROOT = REPO_ROOT / "output"


def _archive_manifest() -> dict[str, str]:
    if not ARCHIVE_ROOT.exists():
        return {}
    return {
        path.relative_to(ARCHIVE_ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(ARCHIVE_ROOT.rglob("*"))
        if path.is_file()
    }


@pytest.fixture(scope="session", autouse=True)
def protect_repository_archive() -> None:
    """Fail the suite if a test mutates the user's real output archive."""

    before = _archive_manifest()
    backup_root = Path(tempfile.mkdtemp(prefix="ai-intel-output-guard-"))
    backup = backup_root / "output"
    if ARCHIVE_ROOT.exists():
        shutil.copytree(ARCHIVE_ROOT, backup)
    try:
        yield
    finally:
        after = _archive_manifest()
        if after != before:
            if ARCHIVE_ROOT.exists():
                shutil.rmtree(ARCHIVE_ROOT)
            if backup.exists():
                shutil.copytree(backup, ARCHIVE_ROOT)
        shutil.rmtree(backup_root, ignore_errors=True)
    if after == before:
        return

    added = sorted(after.keys() - before.keys())
    removed = sorted(before.keys() - after.keys())
    changed = sorted(path for path in before.keys() & after.keys() if before[path] != after[path])
    pytest.fail(
        "tests mutated the repository output archive; use tmp_path/TemporaryDirectory instead: "
        f"added={added[:5]}, removed={removed[:5]}, changed={changed[:5]}"
    )
