from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from .service import (
    briefing_action_purposes,
    briefing_flow_notes,
    briefing_mode_purposes,
    build_dashboard_overview,
    discover_status_payload,
    get_collect_form,
    get_job,
    get_library_item_detail,
    list_collect_sources,
    list_library_items,
    page_purpose_cards,
    preview_briefing,
    PreviewError,
    read_item_markdown,
    run_collect,
    run_discover_from_request,
    save_briefing,
    start_discover_job,
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
                page = int(params.get("page", [1])[0]) if params.get("page") else 1
                page_size = int(params.get("page_size", [20])[0]) if params.get("page_size") else 20
                payload = list_library_items(
                    output_root,
                    keyword=params.get("keyword", [None])[0],
                    sources=sources,
                    since=params.get("since", [None])[0],
                    until=params.get("until", [None])[0],
                    page=page,
                    page_size=page_size,
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
            if parsed.path == "/api/library/preview":
                # Serve the raw Markdown file for an item sidecar. Output is
                # text/markdown (not JSON) so the frontend can display it
                # verbatim without re-parsing JSON quoting.
                output_path = unquote(params.get("output_path", [""])[0])
                try:
                    body, content_type = read_item_markdown(output_root, output_path)
                except PreviewError as exc:
                    _json_response(self, {"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                    return
                except FileNotFoundError as exc:
                    _json_response(self, {"error": str(exc)}, status=HTTPStatus.NOT_FOUND)
                    return
                content = body.encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(content)))
                # No CORS / no cache — same-origin fetch from the workspace UI.
                self.end_headers()
                self.wfile.write(content)
                return
            if parsed.path == "/api/collect/sources":
                _json_response(self, list_collect_sources())
                return
            if parsed.path == "/api/briefing/metadata":
                _json_response(
                    self,
                    {
                        "flow_notes": briefing_flow_notes(),
                        "mode_purposes": briefing_mode_purposes(),
                        "action_purposes": briefing_action_purposes(),
                    },
                )
                return
            if parsed.path == "/api/page-purposes":
                _json_response(self, page_purpose_cards())
                return
            if parsed.path == "/api/discover/status":
                _json_response(self, discover_status_payload(output_root))
                return
            if parsed.path == "/api/discover/job":
                job_id = parse_qs(parsed.query).get("id", [""])[0]
                record = get_job(job_id) if job_id else None
                if record is None:
                    _json_response(self, {"error": "unknown job"}, status=HTTPStatus.NOT_FOUND)
                else:
                    _json_response(self, record)
                return
            if parsed.path.startswith("/api/collect/form/"):
                source = parsed.path.split("/")[-1]
                _json_response(self, get_collect_form(source))
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
            if parsed.path == "/api/collect/run":
                source = payload.get("source", "")
                fields = payload.get("fields", {})
                _json_response(self, run_collect(source, fields, output_root=output_root))
                return
            if parsed.path == "/api/discover/run":
                # Synchronous when ?sync=1 is passed (used by tests); otherwise
                # the work runs on a background thread and the response carries a job_id.
                if parse_qs(parsed.query).get("sync") == ["1"]:
                    _json_response(self, run_discover_from_request(output_root, payload))
                else:
                    _json_response(self, start_discover_job(output_root, payload))
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
    # Resolve `output_root` to an absolute path. If the caller passes a
    # relative path, the resolved value depends on the server's cwd at
    # launch time, which is easy to get wrong (e.g. `python -c ...` started
    # from `web/` would resolve `output` as `web/output`).
    #
    # We anchor relative paths to the project root (the parent of the
    # `workspace_web/` package directory) so the same script works from
    # any cwd. Absolute paths are passed through unchanged.
    project_root = Path(__file__).resolve().parents[1]
    absolute_root = (project_root / output_root).resolve() if not Path(output_root).is_absolute() else Path(output_root).resolve()
    server = ThreadingHTTPServer((host, port), _create_handler(absolute_root))
    print(f"Serving AI Intel Station web workspace on http://{host}:{port}")
    print(f"Using output root: {absolute_root}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web workspace server...")
    finally:
        server.server_close()