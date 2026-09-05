from __future__ import annotations

import sys
import tempfile
import threading
import urllib.request
from html.parser import HTMLParser
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

import ai_intel_station.adapters.web
from ai_intel_station.adapters.web.server import _create_handler


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def _fetch(url: str) -> tuple[int, bytes]:
    with urllib.request.urlopen(url, timeout=5) as response:
        return response.status, response.read()


def main() -> int:
    installed_module = Path(ai_intel_station.adapters.web.__file__).resolve()
    if installed_module.is_relative_to(REPO_ROOT):
        raise AssertionError(
            f"smoke imported repository source instead of installed wheel: {installed_module}"
        )

    with tempfile.TemporaryDirectory() as temp_root:
        server = ThreadingHTTPServer(
            ("127.0.0.1", 0),
            _create_handler(Path(temp_root) / "output"),
        )
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base_url = f"http://127.0.0.1:{int(server.server_address[1])}"
            status, body = _fetch(f"{base_url}/")
            if status != 200:
                raise AssertionError(f"installed Web root returned HTTP {status}")

            html = body.decode("utf-8")
            parser = _AssetReferenceParser()
            parser.feed(html)
            local_assets = [
                urlsplit(reference).path
                for reference in parser.references
                if not urlsplit(reference).scheme
                and urlsplit(reference).path.startswith("/assets/")
            ]
            if not any(path.endswith(".js") for path in local_assets):
                raise AssertionError("installed Web root references no JavaScript asset")
            if not any(path.endswith(".css") for path in local_assets):
                raise AssertionError("installed Web root references no CSS asset")

            for path in local_assets:
                asset_status, asset_body = _fetch(f"{base_url}{path}")
                if asset_status != 200 or not asset_body:
                    raise AssertionError(
                        f"installed Web asset {path} returned HTTP {asset_status} "
                        f"with {len(asset_body)} bytes"
                    )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    print(
        "installed wheel Web smoke passed: "
        f"{installed_module} served {len(local_assets)} referenced assets"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, OSError) as exc:
        print(f"installed wheel smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
