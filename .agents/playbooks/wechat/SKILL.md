---
name: wechat-article-collection
description: Collect WeChat Official Account (微信公众号) articles into the unified research workspace.
author: GitHub Copilot
version: "1.0.0"
tags:
  - wechat
  - 微信
  - 微信文章
  - 公众号
  - markdown
  - research
---

# WeChat Article Collection

Collect a WeChat Official Account article into the unified research workspace.

## Usage

```bash
uv sync --extra wechat
uv run research collect wechat "<WECHAT_ARTICLE_URL>"
```

## Notes

- Runtime entrypoint: `src/ai_intel_station/cli/`
- Source implementation: `src/ai_intel_station/collect/wechat.py`
- WeChat browser dependencies are optional and do not belong to the core runtime
- Root tests: `tests/test_wechat_collect.py` and `tests/test_wechat_e2e_live.py`
