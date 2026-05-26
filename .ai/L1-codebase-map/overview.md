# 项目导航首页

> ⚠️ 每次对话先读本页。这里只回答“去哪看、先读什么”，不展开实现细节。

## 项目身份

- **名称**: AI Intel Station（AI 情报站）
- **做什么**: 通过统一的 workspace 入口完成资料收集、sidecar 回填、本地查询、简报生成和本地 Web 工作台交互
- **技术栈**: Python CLI + uv + pytest(根级 ResearchItem + wechat) + gh CLI + arXiv API + Camoufox / BeautifulSoup / markdownify + React / Vite
- **当前业务结构**: `research/` → `collect/` → `library/` → `briefing/` → `publish/` → `workspace_web/` + `web/`

## 架构约束

```text
禁止：把 output/ 下的生成结果当源码改；要改格式或路径，回到各 fetch 脚本。
禁止：把历史来源工具目录当作真实运行入口；统一 operator surface 在 `research/cli.py`。
禁止：让 briefing 覆盖 output/github、output/papers、output/wechat；派生产物只能写 output/briefing/。
禁止：为查询或简报强制用户重新抓取；历史 Markdown 和 sidecar 必须可复用，必要时先走 `research backfill`。
禁止：改命令、输出路径、依赖前只改代码不改文档；README / SKILL / .ai 必须同步。
```

## 功能索引

| 功能 | 一句话描述 | 详情 | 入口文件 |
| --- | --- | --- | --- |
| 统一研究入口 | 通过一个命令表面组织 collect / query / briefing / backfill | → `features/research-operations/` | `research/cli.py` |
| 微信文章抓取 | 抓取 mp.weixin.qq.com 文章并转成本地 Markdown + images | → `features/wechat-ingestion/` | `collect/wechat.py` |
| GitHub 仓库研究 | 用 `gh` CLI 拉取仓库元数据、议题和搜索结果并落盘 | → `features/github-research/` | `collect/github.py` |
| arXiv 论文抓取 | 按类别拉取最新论文并逐篇保存 Markdown 摘要 | → `features/papers-ingestion/` | `collect/papers.py` |
| 本地资料查询 | 从既有 sidecar 加载统一 ResearchItem，并做关键词 / 来源 / 时间过滤 | → `features/research-query/` | `library/query.py` |
| 简报生成 | 生成适合 Obsidian 阅读的 digest / reading list Markdown | → `features/research-reporting/` | `briefing/main.py` |
| 本地 Web 工作台 | 用 React 提供 Dashboard / Library / Briefing Workspace 三页交互层 | → `features/research-web-workspace/` | `workspace_web/server.py` |
| 输出归档 | 统一管理 `output/` 下各来源的目录结构和生成物边界 | → `features/archive-output/` | `output/` |

## 基础设施索引

| 组件 | 一句话描述 | 详情 |
| --- | --- | --- |
| CLI 运行时 | 根级 `pyproject.toml`、`research` script、workspace 运行约定 | → `infrastructure/cli-runtime/` |
| 外部依赖 | `gh`、Camoufox、arXiv API、网络权限和失败模式 | → `infrastructure/external-dependencies/` |
| 统一内容模型 | `library/items.py` 负责跨来源标准化、sidecar 写入与历史 backfill | → `features/archive-output/` |
| 本地资料库 | `library/storage.py` / `library/query.py` 负责从历史 sidecar 建立查询视图 | → `features/research-query/` |
| Obsidian 交付层 | `briefing/` + `publish/obsidian.py` 负责派生输出，不改变原始归档 | → `features/research-reporting/` |
| 本地 Web 运行时 | `workspace_web/` + `web/` 负责本地 API 桥接、静态资源和 React 交互层 | → `features/research-web-workspace/` |

## 依赖关系概览

```text
基础设施: [CLI 运行时] → [外部依赖]
入口层:   [统一研究入口 / 本地 Web 工作台] → [research/cli.py, workspace_web/server.py]
收集层:   [微信文章抓取 / GitHub 仓库研究 / arXiv 论文抓取] → [collect/*]
资料层:   [本地资料查询] ← [library/items.py, library/storage.py, library/query.py]
简报层:   [简报生成] ← [briefing/*, publish/obsidian.py]
交互层:   [本地 Web 工作台] ← [workspace_web/*, web/*]
输出层:   [输出归档] ← [原始抓取产物, output/briefing 派生产物]
```

## 按需加载导航

```text
收到任务
 ├─ 改统一入口或子命令 → features/research-operations/README.md + research/cli.py
 ├─ 改某个抓取工具 → features/<tool>/README.md
 ├─ 改查询 / 过滤逻辑 → features/research-query/README.md + library/query.py
 ├─ 改 digest / reading list / Obsidian 输出 → features/research-reporting/README.md + briefing/main.py
 ├─ 改 Dashboard / Library / Briefing Web 交互层 → features/research-web-workspace/README.md + workspace_web/server.py + web/
 ├─ 改输出结构或 Markdown 模板 → features/archive-output/README.md + module-map.md
 ├─ 跨工具改命令/依赖/入口 → infrastructure/cli-runtime/README.md + key-files.md
 ├─ 排查网络/认证/浏览器问题 → infrastructure/external-dependencies/README.md + architecture.md
 └─ 写规则、spec、验证文档 → L2 / L3 / L5 对应域文件
```

## 领域术语

| 术语 | 在本项目中的含义 | 容易混淆的点 |
| --- | --- | --- |
| `gh` | GitHub CLI，是 `github-tools` 的真实数据源 | 不是 GitHub REST SDK，也不是本仓库自带模块 |
| Camoufox | 为 WeChat 抓取提供反检测浏览器运行时 | 不是纯 HTTP client，缺环境时会直接影响抓取 |
| `WECHAT_E2E_URLS` | 触发微信 live e2e 的逗号分隔 URL 环境变量 | 不设置时 e2e 测试应跳过，不算失败 |

## 雷区

- 🚫 `output/` — 默认视为生成产物；除非在做归档整理或样例维护，不直接手改
- 🚫 `output/briefing/` — 派生阅读产物；允许重生，不要把它当唯一事实来源
- 🚫 `tools/` 下的来源参考资料 — 只放说明，不放 runtime 代码
- ⚠️ 旧来源工具目录仍可能保留 README / SKILL 等历史资料，但运行入口已经迁到统一 `research` 命令
- ⚠️ `tests/test_wechat_e2e_live.py` 依赖网络、浏览器和 `WECHAT_E2E_URLS`
- ⚠️ Twitter 目前未实现；若后续接入，请先补 `tools/twitter/README.md`、L1/L2/L3/L5 文档，再进入 `collect/` 和统一入口

## 构建和运行

```bash
# Root test entrypoints
uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_wechat_collect.py

# 统一研究入口
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
uv run research collect papers cs.AI --max 10
uv run research collect wechat "<wechat-url>"
uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output

# 本地 Web 工作台
npm --prefix web install
npm --prefix web run build
uv run research web
```
