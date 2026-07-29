# 本地 Web 工作台

## 适用任务

- 改 Dashboard 的本地归档统计、coverage gap 或 recent briefing 展示
- 改 Library 的筛选条件、详情面板字段或本地 sidecar 映射
- 改 Briefing Workspace 的预览、保存和 partial-success 呈现
- 排查本地 Web 启动入口、静态资源、API 桥接为什么失效

## 入口与关键文件

- `research/cli.py` — `web` 子命令的统一入口
- `workspace_web/server.py` — 本地 HTTP 服务、静态资源和 API 路由
- `workspace_web/service.py` — Dashboard / Library / Briefing 的本地桥接逻辑
- `web/src/App.jsx` — React 工作台主界面
- `web/src/styles.css` — Web 工作台视觉层

## 主数据流

```text
research web
  → workspace_web.server.serve_workspace()
  → /api/navigation / /api/dashboard / /api/library / /api/briefing/*
  → workspace_web.service
  → library.query / library.storage / briefing.reports
  → output/ 与 output/briefing/
```

## 关键约束

- Web 工作台只能消费本地 sidecar 和派生 briefing，不在这里触发远程 collect
- Briefing 保存仍只能写 `output/briefing/`
- MVP 导航只包含 Dashboard、Library、Briefing Workspace，不暴露 collect / backfill 控制
- 若前端静态资源未 build，服务端必须明确提示，而不是静默返回空白页

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |
| 改 `research web` 启动参数 | `research/cli.py` + README + overview |
| 改 Dashboard 统计口径 | `workspace_web/service.py` + `tests/test_web_workspace.py` |
| 改 Library 过滤或详情字段 | `library/query.py` + `workspace_web/service.py` + `tests/test_web_workspace.py` |
| 改 Briefing 预览或保存流程 | `briefing/reports.py` + `workspace_web/service.py` + `tests/test_web_workspace.py` |
| 改前端布局或视觉 | `web/src/App.jsx` + `web/src/styles.css` |

## 验证

```bash
python3 -m pytest tests/test_web_workspace.py
npm --prefix web install
npm --prefix web run build
uv run research web
```

## 已知边界

- 当前 Web 工作台仍是本地单机模式，不支持远程 API 服务或多用户协作
- 当前 collect / backfill 仍保留在 CLI，不进入第一期 Web MVP
