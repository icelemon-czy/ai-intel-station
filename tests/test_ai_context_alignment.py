from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_active_ai_context_is_free_of_patch_markers() -> None:
    active_files = [
        REPO_ROOT / ".ai" / "L3-specs" / "specs" / "system.md",
        REPO_ROOT / ".ai" / "L2-rules" / "testing.md",
        REPO_ROOT / ".ai" / "L5-validation" / "validation-rules.md",
    ]

    for path in active_files:
        assert "*** Add File:" not in path.read_text(encoding="utf-8"), path.as_posix()


def test_ai_context_uses_a_single_workflow_source_of_truth() -> None:
    assert not (REPO_ROOT / ".ai" / ".github").exists()
