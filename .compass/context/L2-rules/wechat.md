# WeChat 模块规则

## 公开契约

- CLI 命令：`uv run research collect wechat "<wechat-url>"`
- Optional runtime：`uv sync --extra wechat`
- operator 入口：`research/cli.py`
- 公开入口：`fetch_article()`、`normalize_wechat_url()`
- 默认输出：`output/wechat/<文章标题>/`

## 修改边界

- URL 预处理规则改动必须补 `tests/test_wechat_collect.py`
- 输出目录或 Markdown 字段改动必须同步 `README.md`、`SKILL.md`、`.compass/context` 文档
- 子命令参数变化要同时检查 `research/cli.py` dispatch

## 风险点

- Camoufox / 页面结构变化会直接导致抓取失效
- 未安装 `wechat` extra 时必须返回明确 install guidance，不影响 core command 或其他 source
- 图片下载和 Markdown 替换是两段逻辑，缺图不一定是抓 HTML 失败
- live e2e 依赖环境，不是默认 CI 保护网

## 推荐验证

```bash
uv run --extra wechat --extra dev python -m pytest tests/test_wechat_collect.py
WECHAT_E2E_URLS="<wechat-url>" uv run --extra wechat --extra dev python -m pytest tests/test_wechat_e2e_live.py -m e2e
```
