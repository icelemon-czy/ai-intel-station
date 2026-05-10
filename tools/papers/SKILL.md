# arXiv Papers Skill

Fetch and save AI/ML papers from arXiv by category inside the unified research workspace.

## Usage

```bash
uv run research collect papers --list
uv run research collect papers cs.AI --max 10
uv run research collect papers cs.LG cs.CL --max 20
```

## Notes

- Runtime entrypoint: `research/cli.py`
- Source implementation: `collect/papers.py`
- Uses the arXiv public API and defaults to 10 papers per category