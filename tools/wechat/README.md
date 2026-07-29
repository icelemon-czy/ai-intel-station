# WeChat Source Notes

Reference notes for the WeChat collection source inside the research workspace.

## Runtime Path

```bash
uv sync --extra wechat
uv run research collect wechat "https://mp.weixin.qq.com/s/xxxxxxxx"
```

## Output

```text
output/
└── wechat/
    └── <article-title>/
        ├── <article-title>.md
        ├── research-item.json
        └── images/
```

## Notes

- Runtime entrypoint: `research/cli.py`
- Source implementation: `collect/wechat.py`
- Missing optional runtime returns `uv sync --extra wechat` guidance without affecting other sources
- Root tests: `tests/test_wechat_collect.py` and `tests/test_wechat_e2e_live.py`
