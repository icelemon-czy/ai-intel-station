# 外部依赖

## 依赖清单

| 依赖 | 被谁使用 | 作用 | 典型失败信号 |
|------|----------|------|--------------|
| Camoufox（`wechat` extra） | wechat | 绕过 WeChat 抓取限制并获取页面 HTML | 未安装 extra、浏览器启动失败、抓取不到正文 |
| BeautifulSoup / markdownify / httpx（`wechat` extra） | wechat | 解析、转换并下载图片 | 未安装 extra、图片缺失、链接未重写 |
| `gh` CLI | github | 查询仓库、议题、搜索结果 | `run_gh()` 抛 `RuntimeError` |
| arXiv search API + official category Atom feed | papers | 拉取最新 paper evidence；search API throttle/timeout 时使用 daily feed fallback | search 与 fallback 都失败后某类别打印 `Failed to fetch` |
| Hacker News public API | hackernews discovery | 拉取 bounded feed 与 item JSON | malformed / unavailable response 记 source failure |
| WeChat public index | wechat discovery | best-effort account watchlist discovery | CAPTCHA、access block、空页、缺 publication time |
| X recent-search API | optional x discovery | 拉取 bounded recent Posts | token 缺失或 remote failure；其他 source 继续 |
| 网络访问 | 全部抓取工具 | 访问远程源 | 命令超时、空输出、解析失败 |

## 先验检查

```bash
gh auth status
uv run research collect papers --list
uv sync --extra wechat
uv run --extra wechat --extra dev python -m pytest tests/test_wechat_collect.py
```

## 故障分类

1. **认证型**: GitHub 工具最常见，先看 `gh` 是否登录。
2. **optional browser runtime 型**: 只影响 wechat；先确认 `wechat` extra，再排查 Camoufox 或页面反爬。
3. **公开 API / 网络型**: HN、Papers、WeChat index、X 都可能失败；daily runtime 必须独立记录 source coverage。
4. **格式漂移型**: 外部页面结构变了，现有解析逻辑和测试不再匹配。

## 修改原则

- 不要把外部依赖问题伪装成输出层问题；先定位在哪个边界失败
- source-specific heavy dependency 放入对应 optional extra，不得阻止 core CLI startup
- credential value 不写入 config；X 只读取明确配置的 token environment variable，未启用时不读取
- 依赖检查命令写进文档后，代码改动时要保持它们仍然可用
- 如果某项依赖变成新的硬前置条件，要同步更新 feature README、L2 规则和 L3 spec
