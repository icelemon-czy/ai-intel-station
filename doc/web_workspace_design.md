# Web Workspace

Web Workspace 是 optional local viewer。它复用同一套 Python service、local archive 和 briefing runtime，为不想只用 CLI 的场景提供 Dashboard、Library、Briefing、Collect 和 Daily Discovery UI；日常 Agent-first flow 不依赖它。

```text
React UI (web/)
      ↓ JSON / Markdown HTTP
workspace_web server + service
      ↓
collect / library / briefing / discovery
      ↓
local output/ + local run log
```

## 页面 boundary

| Surface | Reads | Produces |
|:--------|:------|:---------|
| Dashboard | local sidecar、recent briefing | archive count、missing source、orphan Markdown、empty state |
| Library | local sidecar | filter result、item detail、saved Markdown preview |
| Briefing Workspace | local Library | preview；显式 Save 后写 briefing Markdown |
| Collect Workspace | GitHub / arXiv / WeChat input | source-specific archive 与 sidecar |
| Daily Discovery | discovery config、run log | background run、pollable status、signal briefing |

Library 和 Briefing 不触发 remote fetch；Collect 和 Daily Discovery 才会访问 source。HTTP error 使用结构化 JSON 返回 user-visible failure，避免把 Python traceback 当成 UI contract。

## Runtime boundary

- `web/` 包含 React source 和 Node tests。
- `npm --prefix web run build` 生成 static bundle。
- Python package 内的 `workspace_web/static/` 是 runtime serving artifact，并由 release check 验证引用完整。
- `research web` 启动 local `ThreadingHTTPServer`，默认绑定 `127.0.0.1:4173`。
- relative output root 固定锚定 project root，避免从不同 cwd 启动时读取错误目录。

## Daily Discovery job

Web POST 默认创建 background thread 并立即返回 `job_id`；UI 轮询 job/status endpoint。In-memory registry 只保留有限数量的 recent job，并只驱逐 finished job。同步 endpoint 仅用于 tests 和明确调用。

## 安全与 ownership

- Markdown preview 只能读取 output root 下的文件，拒绝 path traversal 和缺失文件。
- Web service 复用 production collector/query/briefing function，不维护第二套业务规则。
- Web 只是 optional adapter；CLI 和 Agent flow 在未构建 frontend 时仍可使用。

## 入口与 evidence

构建 frontend bundle 后，通过统一 CLI 启动 local server：

```bash
npm --prefix web install
npm --prefix web run build
uv run research web
```

- Backend：`workspace_web/server.py`、`workspace_web/service.py` facade 与 `workspace_web/<feature>.py`
- Frontend：`web/src/App.jsx` composition 与 `web/src/*Section.jsx`
- Tests：`tests/test_web_backend.py`、`tests/test_web_http_preview.py`、`tests/test_http_*_e2e.py`、`tests/test_service_e2e.py`、`web/test/`（frontend behavior owner）
