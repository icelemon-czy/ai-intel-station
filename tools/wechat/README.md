# WeChat Source Notes

Reference notes for the WeChat collection source inside the research workspace.

## Runtime Path

```bash
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
- Root tests: `tests/test_wechat_collect.py` and `tests/test_wechat_e2e_live.py`
