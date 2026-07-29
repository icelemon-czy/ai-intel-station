from pathlib import Path

import pytest

from scripts.check_release_artifacts import _assert_web_assets


ARTIFACT = Path("ai_intel_station-test.whl")


def test_artifact_checker_requires_every_referenced_hashed_asset() -> None:
    names = [
        "workspace_web/static/index.html",
        "workspace_web/static/assets/app-valid.js",
        "workspace_web/static/assets/app-valid.css",
    ]
    html = """
    <script type="module" src="/assets/app-missing.js"></script>
    <link rel="stylesheet" href="/assets/app-valid.css">
    """

    with pytest.raises(AssertionError, match="app-missing.js"):
        _assert_web_assets(names, html, artifact=ARTIFACT)


def test_artifact_checker_accepts_packaged_assets_referenced_by_index() -> None:
    names = [
        "workspace_web/static/index.html",
        "workspace_web/static/assets/app-valid.js",
        "workspace_web/static/assets/app-valid.css",
    ]
    html = """
    <script type="module" src="/assets/app-valid.js"></script>
    <link rel="stylesheet" href="/assets/app-valid.css">
    """

    _assert_web_assets(names, html, artifact=ARTIFACT)
