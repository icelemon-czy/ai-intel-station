# Twitter Source Notes

Twitter collection is not implemented in this workspace.

If this source is added later, implement it through the business layers first:

- `collect/` for ingestion
- `library/` for `ResearchItem` sidecars
- `research/cli.py` for the operator-facing command surface

Do not reintroduce a top-level `twitter-tools/` runtime surface.
