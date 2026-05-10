# GitHub Collection Skill

Collect and save GitHub repository information as Markdown inside the unified research workspace.

## Usage

```bash
uv run research collect github owner/repo
uv run research collect github "query" --search
```

## Notes

- Runtime entrypoint: `research/cli.py`
- Source implementation: `collect/github.py`
- `gh` CLI must be installed and authenticated