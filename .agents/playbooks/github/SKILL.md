# GitHub Collection Skill

Collect and save GitHub repository information as Markdown inside the unified research workspace.

## Usage

```bash
uv run research collect github owner/repo
uv run research collect github "query" --search
```

## Notes

- Runtime entrypoint: `src/ai_intel_station/cli/`
- Source implementation: `src/ai_intel_station/collect/github.py`
- `gh` CLI must be installed and authenticated