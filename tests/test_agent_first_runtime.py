from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from research.discovery import EXAMPLE_CONFIG_PATH


REPO_ROOT = Path(__file__).resolve().parents[1]


def _toml_section(text: str, name: str) -> str:
    marker = f"[{name}]"
    start = text.index(marker) + len(marker)
    next_section = text.find("\n[", start)
    return text[start:] if next_section < 0 else text[start:next_section]


def _toml_array(section: str, key: str) -> list[str]:
    assignment = section.index(f"{key} =")
    start = section.index("[", assignment)
    depth = 0
    quote: str | None = None
    escaped = False

    for index in range(start, len(section)):
        char = section[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                value = ast.literal_eval(section[start : index + 1])
                return list(value)

    raise AssertionError(f"unterminated TOML array for {key}")


class AgentFirstRuntimeContractTests(unittest.TestCase):
    def test_default_dependency_set_excludes_optional_and_test_stacks(self) -> None:
        text = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        project = _toml_section(text, "project")
        extras = _toml_section(text, "project.optional-dependencies")

        self.assertEqual(_toml_array(project, "dependencies"), ["PyYAML>=6.0"])
        self.assertEqual(
            set(_toml_array(extras, "wechat")),
            {"camoufox[geoip]", "markdownify", "beautifulsoup4", "httpx"},
        )
        self.assertEqual(_toml_array(extras, "dev"), ["pytest>=7.0"])

    def test_wechat_extra_frozen_sync_plan_contains_full_runtime_stack(self) -> None:
        uv = shutil.which("uv")
        self.assertIsNotNone(uv, "uv is required to validate project packaging")

        with tempfile.TemporaryDirectory() as env_root:
            environment = dict(os.environ)
            environment.update(
                {
                    "UV_PROJECT_ENVIRONMENT": str(Path(env_root) / "venv"),
                    "UV_CACHE_DIR": str(Path(env_root) / "cache"),
                    "UV_OFFLINE": "1",
                }
            )
            result = subprocess.run(
                [
                    str(uv),
                    "sync",
                    "--extra",
                    "wechat",
                    "--dry-run",
                    "--frozen",
                ],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )

        rendered = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0, rendered)
        for package in (
            "beautifulsoup4",
            "camoufox",
            "httpx",
            "markdownify",
            "playwright",
        ):
            self.assertIn(package, rendered.lower())

    def test_core_dry_run_does_not_import_optional_packages(self) -> None:
        example = EXAMPLE_CONFIG_PATH
        with tempfile.TemporaryDirectory() as temp_root:
            config = Path(temp_root) / "discovery.yaml"
            config.write_text(
                example.read_text(encoding="utf-8").replace(
                    "log_dir: .state/discovery",
                    f"log_dir: {Path(temp_root) / 'logs'}",
                    1,
                ),
                encoding="utf-8",
            )
            code = f"""
import builtins
real_import = builtins.__import__
blocked = {{"camoufox", "bs4", "markdownify", "httpx", "pytest"}}
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in blocked:
        raise AssertionError(f"optional package imported by core flow: {{name}}")
    return real_import(name, globals, locals, fromlist, level)
builtins.__import__ = guarded_import
from research.cli import main
raise SystemExit(main(["discover", "--dry-run", "--config", {str(config)!r}]))
"""
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("dry-run", result.stdout.lower())

    def test_missing_wechat_extra_returns_guidance_without_traceback(self) -> None:
        code = """
import builtins
real_import = builtins.__import__
blocked = {"camoufox", "bs4", "markdownify", "httpx"}
def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if name.split(".", 1)[0] in blocked:
        raise ModuleNotFoundError(
            f"blocked optional package: {name}",
            name=name.split(".", 1)[0],
        )
    return real_import(name, globals, locals, fromlist, level)
builtins.__import__ = guarded_import
from research.cli import main
raise SystemExit(
    main(["collect", "wechat", "https://mp.weixin.qq.com/s/example"])
)
"""
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        rendered = result.stdout + result.stderr
        self.assertEqual(result.returncode, 2, rendered)
        self.assertIn("uv sync --extra wechat", rendered)
        self.assertNotIn("Traceback", rendered)

    def test_daily_discovery_skill_executes_instead_of_teaching_commands(self) -> None:
        canonical = REPO_ROOT / ".agents" / "skills" / "daily-discovery" / "SKILL.md"
        text = canonical.read_text(encoding="utf-8")

        self.assertIn("Agent 读取 artifact", text)
        self.assertIn("不要让用户自己", text)
        self.assertIn("不启动 Web", text)
        self.assertIn("只有用户明确要求 install", text)
        self.assertIn("只抓取这个微信公众号 URL", text)
        self.assertIn("dry-run log", text)
        self.assertIn("不能把旧内容包装成今天的 briefing", text)
        self.assertIn("保留未涉及的 field", text)
        self.assertIn("不要替用户扩大关注范围", text)
        self.assertIn("修改后必须 dry-run validation", text)
        self.assertIn("ready|partial|no_fresh_signals|coverage_incomplete", text)
        self.assertIn("`dry_run`、`failed`、`legacy`", text)
        self.assertIn("覆盖不完整，无法得出今日无新内容的结论", text)
        self.assertIn("github|papers|wechat|hackernews|x", text)
        self.assertIn("最多 7 条", text)
        self.assertIn("optional、最多 2 条 WeChat", text)
        self.assertIn("expected / actual / missing", text)
        self.assertIn("arXiv / GitHub / Hacker News / WeChat", text)
        self.assertIn("不得改报成 GitHub news", text)
        self.assertNotIn("destination excluded", text)
        self.assertNotIn("5 News", text)
        self.assertNotIn("github_news_max_items", text)

        for platform_root in (".claude", ".github"):
            wrapper = (
                REPO_ROOT / platform_root / "skills" / "daily-discovery" / "SKILL.md"
            )
            wrapper_text = wrapper.read_text(encoding="utf-8")
            self.assertIn(
                "../../../.agents/skills/daily-discovery/SKILL.md",
                wrapper_text,
            )
            self.assertTrue(canonical.is_file())
            self.assertNotIn("让用户用 `$EDITOR`", wrapper_text)

    def test_validation_workflow_matches_agent_first_dependency_boundaries(self) -> None:
        workflow = (
            REPO_ROOT / ".github" / "workflows" / "validate.yml"
        ).read_text(encoding="utf-8")

        self.assertIn(".agents/skills", workflow)
        self.assertNotIn(".Codex/skills", workflow)
        for job in ("core-tests:", "wechat-tests:", "web-tests:"):
            self.assertIn(job, workflow)
        self.assertIn("uv sync --extra dev --frozen", workflow)
        self.assertIn("uv sync --extra dev --extra wechat --frozen", workflow)
        self.assertIn("--ignore=tests/test_discovery_runner.py", workflow)
        self.assertIn("tests.test_discovery_runner -v", workflow)
        self.assertIn("npm ci", workflow)
        self.assertIn("npm run build", workflow)
        self.assertIn("npm test", workflow)


if __name__ == "__main__":
    unittest.main()
