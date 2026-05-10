# Papers Source Notes

Reference notes for the arXiv papers collection source inside the research workspace.

## Runtime Path

```bash
uv run research collect papers --list
uv run research collect papers cs.AI --max 10
uv run research collect papers cs.LG cs.CL --max 20
```

## Notes

- Runtime entrypoint: `research/cli.py`
- Source implementation: `collect/papers.py`
- Uses the arXiv public API and continues across category-level failures
