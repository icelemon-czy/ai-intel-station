# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试。

- [x] 1.1 preview endpoint returns Markdown for a known sidecar path
- [x] 1.2 preview endpoint rejects paths outside output_root
- [x] 1.3 preview endpoint rejects paths not present in any sidecar
- [x] 1.4 preview endpoint returns 404 when file is missing
- [x] 1.5 Library detail panel renders a preview region
- [x] 1.6 Library detail panel shows a clear error for unreadable Markdown
- [x] 1.7 preview does not modify state

## 2. Backend (workspace_web service + server)

- [x] 2.1 在 `workspace_web/service.py` 增加 `read_item_markdown(output_root, output_path)` 函数
  - 校验路径在 output_root 内（防 path traversal）
  - 校验路径是某个已加载 sidecar 的 output_path
  - 读文件 + 返回 `(content, content_type)` 或抛 `PreviewError`
- [x] 2.2 在 `workspace_web/server.py` 增加 `GET /api/library/preview?output_path=...` 端点
  - 200 + text/markdown
  - 400 (path traversal) / 404 (not a sidecar or file missing)

## 3. Frontend (App.jsx)

- [x] 3.1 Library 详情面板加 `<MarkdownPreview>` 区域（在 "View Markdown" 按钮位置或下面）
- [x] 3.2 选中 item 时 fetch preview，显示 loading / content / error 三态
- [x] 3.3 Markdown 内容用 `<pre>` 渲染（不引入 markdown 库以保持零依赖；后续可换 react-markdown）

## 4. Wire it up

- [x] 4.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 4.2 跑 `web/test/*.test.mjs` 全绿
- [x] 4.3 端到端：浏览器选 Library item，preview 区域显示正文

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
