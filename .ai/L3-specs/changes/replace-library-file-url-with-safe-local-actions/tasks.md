# Implementation Tasks

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试。

- [x] 1.1 detail-actions do NOT contain file:// references
- [x] 1.2 detail-actions offer Preview Markdown
- [x] 1.3 detail-actions offer Open source link
- [x] 1.4 detail-actions offer Copy archive path with clipboard API
- [x] 1.5 clipboard API failure falls back gracefully
- [x] 1.6 about-local-files note is visible
- [x] 1.7 clipboard call uses navigator.clipboard.writeText

## 2. Frontend (App.jsx)

- [x] 2.1 在 detail-actions 增加 `Copy archive path` 按钮
- [x] 2.2 实现 `handleCopy` 用 `navigator.clipboard.writeText` + 失败回退（try/catch + 状态文案）
- [x] 2.3 "Copied" 状态显示至少 1 秒后自动恢复
- [x] 2.4 加 `AboutLocalFilesNote` 组件（small eyebrow 解释）
- [x] 2.5 删除/保留 #1 加的 `Open source link` anchor（已存在，但确认仍在）

## 3. Wire it up

- [x] 3.1 跑 `tests/test_web_workspace.py` 全绿
- [x] 3.2 跑 `web/test/*.test.mjs` 全绿
- [x] 3.3 端到端：浏览器点 Copy archive path，剪贴板有 path，显示 "Copied"

<!--
规则：
- 每个任务必须是 checkbox：`- [ ] X.Y 描述`
- 第一组固定为 Tests — 从 Scenario 的 WHEN/THEN 映射
- 后续组为实现步骤，按依赖顺序排列
- 任务要小到一轮对话能完成
- TDD 纪律：先写测试（红）→ 再实现代码（绿）
-->
