# GitHub Source Notes

Reference notes for the GitHub collection source inside the research workspace.

## Runtime Path

```bash
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
```

## Notes

- Runtime entrypoint: `research/cli.py`
- Source implementation: `collect/github.py`
- Requires local `gh` CLI authentication
