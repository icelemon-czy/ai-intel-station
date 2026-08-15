# WeChat 模块规则

## 公开契约

- CLI 命令：`uv run research collect wechat "<wechat-url>"`
- Optional runtime：`uv sync --extra wechat`
- operator 入口：`research/cli.py`
- 公开入口：`fetch_article()`、`normalize_wechat_url()`
- 默认输出：`output/wechat/<文章标题>/`
- Daily watchlist：`sources.wechat.accounts` 通过 best-effort public-index adapter discovery；不新增 standalone collect subcommand

## 修改边界

- URL 预处理规则改动必须补 `tests/test_wechat_collect.py`
- 输出目录或 Markdown 字段改动必须同步 `README.md`、`SKILL.md`、`.compass/context` 文档
- 子命令参数变化要同时检查 `research/cli.py` dispatch
- account-index item 必须可归属到 configured account，并保存 publication time、watchlist 与 discovery method

## 风险点

- Camoufox / 页面结构变化会直接导致抓取失效
- 未安装 `wechat` extra 时必须返回明确 install guidance，不影响 core command 或其他 source
- 图片下载和 Markdown 替换是两段逻辑，缺图不一定是抓 HTML 失败
- live e2e 依赖环境，不是默认 CI 保护网
- public index 出现 CAPTCHA、access block、empty/malformed response 或 missing publication time 时必须记 coverage failure；不得解释为公众号今天无更新

## 推荐验证

```bash
uv run --extra wechat --extra dev python -m pytest tests/test_wechat_collect.py
uv run --extra dev python -m pytest -q tests/test_realtime_signals.py
WECHAT_E2E_URLS="<wechat-url>" uv run --extra wechat --extra dev python -m pytest tests/test_wechat_e2e_live.py -m e2e
```
