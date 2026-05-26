# AI Intel Station

`ai-intel-station` is a local-first AI intelligence workspace for collecting source material, building a shared library, and generating Obsidian-friendly briefings.

## Business Flow

1. `collect` gathers raw material from GitHub, arXiv, or WeChat into `output/<source>/`
2. `query` searches local `ResearchItem` sidecars without re-fetching remote data
3. `briefing` generates digest or reading-list Markdown under `output/briefing/`
4. `backfill` rebuilds sidecars from historical Markdown archives
5. `web` serves a local React workspace for dashboard, library browsing, and briefing generation

## Unified Runtime Surface

```bash
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
uv run research collect papers cs.AI --max 10
uv run research collect wechat "https://mp.weixin.qq.com/s/example"

uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output

# Build the local React workspace, then serve it
npm --prefix web install
npm --prefix web run build
uv run research web
```

## Output Layout

```text
output/
  ├─ github/
  ├─ papers/
  ├─ wechat/
  └─ briefing/
```

Raw archives remain source-segregated. Derived reading artifacts are written only under `output/briefing/`.

## Local Web Workspace

The first-phase local web workspace keeps the same local-first rules as the CLI:

1. Dashboard reads local sidecars and recent briefing artifacts only.
2. Library reuses local `ResearchItem` search without remote fetches.
3. Briefing Workspace previews and saves derived Markdown under `output/briefing/`.

Use one of these startup paths:

```bash
# Production-like local run
npm --prefix web install
npm --prefix web run build
uv run research web

# Frontend development with API proxy
uv run research web
npm --prefix web run dev
```
