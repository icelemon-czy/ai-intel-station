from __future__ import annotations

import sys
import tarfile
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


DIST_DIR = Path(__file__).resolve().parents[1] / "dist"
FORBIDDEN_PARTS = {
    ".agents",
    ".ai",
    ".compass",
    ".state",
    "config/discovery.yaml",
    "output",
}


def _single(pattern: str) -> Path:
    matches = sorted(DIST_DIR.glob(pattern))
    if len(matches) != 1:
        raise AssertionError(
            f"expected one {pattern} artifact in {DIST_DIR}, found {matches}"
        )
    return matches[0]


def _assert_runtime_boundary(names: list[str], *, artifact: Path) -> None:
    normalized = [name.strip("/") for name in names]
    for forbidden in FORBIDDEN_PARTS:
        if any(
            name == forbidden
            or name.startswith(f"{forbidden}/")
            or name.endswith(f"/{forbidden}")
            or f"/{forbidden}/" in name
            for name in normalized
        ):
            raise AssertionError(f"{artifact.name} contains private path {forbidden!r}")


class _AssetReferenceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "script" and values.get("src"):
            self.references.append(values["src"])
        if tag == "link" and values.get("href"):
            self.references.append(values["href"])


def _static_entry_name(names: list[str], suffix: str) -> str:
    matches = [
        name
        for name in names
        if name.strip("/").endswith(f"ai_intel_station/adapters/web/static/{suffix}")
    ]
    if len(matches) != 1:
        raise AssertionError(f"expected one packaged static entry {suffix!r}, found {matches}")
    return matches[0]


def _assert_web_assets(
    names: list[str],
    index_html: str,
    *,
    artifact: Path,
) -> None:
    normalized = [name.strip("/") for name in names]
    static_names = [
        name[name.index("ai_intel_station/adapters/web/static/") :]
        for name in normalized
        if "ai_intel_station/adapters/web/static/" in name
    ]
    required = "ai_intel_station/adapters/web/static/index.html"
    if required not in static_names:
        raise AssertionError(f"{artifact.name} is missing {required}")

    parser = _AssetReferenceParser()
    parser.feed(index_html)
    local_assets: list[str] = []
    for reference in parser.references:
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc:
            continue
        relative = parsed.path.lstrip("/")
        if relative.startswith("./"):
            relative = relative[2:]
        if relative.startswith("assets/"):
            local_assets.append(f"ai_intel_station/adapters/web/static/{relative}")

    if not any(name.endswith(".js") for name in local_assets):
        raise AssertionError(f"{artifact.name} index.html references no local JavaScript asset")
    if not any(name.endswith(".css") for name in local_assets):
        raise AssertionError(f"{artifact.name} index.html references no local CSS asset")

    missing = sorted(set(local_assets) - set(static_names))
    if missing:
        raise AssertionError(
            f"{artifact.name} index.html references missing packaged assets: {missing}"
        )


def main() -> int:
    wheel = _single("ai_intel_station-*.whl")
    source = _single("ai_intel_station-*.tar.gz")

    with zipfile.ZipFile(wheel) as archive:
        wheel_names = archive.namelist()
        wheel_index = archive.read(
            _static_entry_name(wheel_names, "index.html")
        ).decode("utf-8")
    with tarfile.open(source, mode="r:gz") as archive:
        source_names = archive.getnames()
        source_member = archive.extractfile(
            _static_entry_name(source_names, "index.html")
        )
        if source_member is None:
            raise AssertionError(f"{source.name} index.html is not a regular file")
        source_index = source_member.read().decode("utf-8")

    for artifact, names, index_html in (
        (wheel, wheel_names, wheel_index),
        (source, source_names, source_index),
    ):
        _assert_runtime_boundary(names, artifact=artifact)
        _assert_web_assets(names, index_html, artifact=artifact)

    print(
        "release artifacts verified: "
        f"{wheel.name} ({wheel.stat().st_size} bytes), "
        f"{source.name} ({source.stat().st_size} bytes)"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"release artifact check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
