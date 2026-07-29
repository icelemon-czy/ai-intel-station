from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_active_ai_context_is_free_of_patch_markers() -> None:
    active_files = [
        REPO_ROOT / ".compass" / "context" / "L3-specs" / "specs" / "system.md",
        REPO_ROOT / ".compass" / "context" / "L2-rules" / "testing.md",
        REPO_ROOT / ".compass" / "context" / "L5-validation" / "validation-rules.md",
    ]

    for path in active_files:
        assert "*** Add File:" not in path.read_text(encoding="utf-8"), path.as_posix()


def test_ai_context_uses_a_single_workflow_source_of_truth() -> None:
    assert not (REPO_ROOT / ".compass" / "context" / ".github").exists()
    assert not (REPO_ROOT / ".ai").exists()
    assert not (REPO_ROOT / ".codex" / "legacy-skills").exists()

    for platform_root in (".github", ".claude"):
        skill_root = REPO_ROOT / platform_root / "skills"
        assert sorted(path.name for path in skill_root.iterdir()) == [
            "daily-discovery"
        ]


def test_installed_compass_footprint_and_context_maintenance_are_compatible() -> None:
    compass_root = REPO_ROOT / ".compass"
    assert sorted(path.name for path in compass_root.iterdir()) == ["context"]

    build_context = (
        REPO_ROOT / ".agents" / "skills" / "build-context" / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert "稳定运行不得依赖" in build_context
    assert "确认 `.compass/context/` 存在" in build_context
    assert "确认 `.compass/INSTALL.md` 和 `.compass/context/` 存在" not in build_context


def test_platform_launch_configuration_contains_no_personal_absolute_path() -> None:
    launch = (REPO_ROOT / ".claude" / "launch.json").read_text(encoding="utf-8")
    assert "/Users/" not in launch
    assert '"runtimeExecutable": ".venv/bin/python"' in launch
    assert "Path('output')" in launch
