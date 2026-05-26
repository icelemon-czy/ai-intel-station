from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .service import (
    build_dashboard_overview,
    get_library_item_detail,
    list_library_items,
    preview_briefing,
    save_briefing,
    workspace_sections,
)


STATIC_DIR = Path(__file__).resolve().parent / "static"


def _json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def _json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = HTTPStatus.OK) -> None:
    content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


def _text_response(handler: BaseHTTPRequestHandler, body: str, status: int = HTTPStatus.OK) -> None:
    content = body.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "text/plain; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


def _serve_file(handler: BaseHTTPRequestHandler, file_path: Path) -> None:
    content = file_path.read_bytes()
    content_type, _ = mimetypes.guess_type(file_path.name)
    handler.send_response(HTTPStatus.OK)
    handler.send_header("Content-Type", f"{content_type or 'application/octet-stream'}; charset=utf-8")
    handler.send_header("Content-Length", str(len(content)))
    handler.end_headers()
    handler.wfile.write(content)


def _create_handler(output_root: Path):
    class WorkspaceHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)

            if parsed.path == "/api/navigation":
                _json_response(self, workspace_sections())
                return
            if parsed.path == "/api/dashboard":
                _json_response(self, build_dashboard_overview(output_root))
                return
            if parsed.path == "/api/library":
                sources = params.get("source") or None
                payload = list_library_items(
                    output_root,
                    keyword=params.get("keyword", [None])[0],
                    sources=sources,
                    since=params.get("since", [None])[0],
                    until=params.get("until", [None])[0],
                )
                _json_response(self, payload)
                return
            if parsed.path == "/api/library/item":
                output_path = unquote(params.get("output_path", [""])[0])
                payload = get_library_item_detail(output_root, output_path)
                if payload is None:
                    _json_response(self, {"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
                    return
                _json_response(self, payload)
                return
            if parsed.path.startswith("/api/"):
                _json_response(self, {"error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)
                return

            self._serve_static(parsed.path)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            payload = _json_body(self)

            if parsed.path == "/api/briefing/preview":
                _json_response(
                    self,
                    preview_briefing(
                        output_root,
                        mode=payload.get("mode", "digest"),
                        keyword=payload.get("keyword", ""),
                        title=payload.get("title"),
                        sources=payload.get("sources"),
                        since=payload.get("since"),
                        until=payload.get("until"),
                    ),
                )
                return
            if parsed.path == "/api/briefing/save":
                _json_response(
                    self,
                    save_briefing(
                        output_root,
                        mode=payload.get("mode", "digest"),
                        keyword=payload.get("keyword", ""),
                        title=payload.get("title"),
                        sources=payload.get("sources"),
                        since=payload.get("since"),
                        until=payload.get("until"),
                    ),
                )
                return
            _json_response(self, {"error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)

        def log_message(self, format: str, *args: object) -> None:
            return

        def _serve_static(self, request_path: str) -> None:
            index_path = STATIC_DIR / "index.html"
            if not index_path.exists():
                _text_response(
                    self,
                    "Frontend assets are missing. Run `npm --prefix web install && npm --prefix web run build` first.",
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                )
                return

            cleaned = request_path.lstrip("/")
            candidate = (STATIC_DIR / cleaned).resolve()
            if cleaned and candidate.exists() and candidate.is_file() and STATIC_DIR in candidate.parents:
                _serve_file(self, candidate)
                return
            _serve_file(self, index_path)

    return WorkspaceHandler


def serve_workspace(output_root: Path, host: str = "127.0.0.1", port: int = 4173) -> None:
    server = ThreadingHTTPServer((host, port), _create_handler(Path(output_root)))
    print(f"Serving AI Intel Station web workspace on http://{host}:{port}")
    print(f"Using output root: {Path(output_root)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web workspace server...")
    finally:
        server.server_close()