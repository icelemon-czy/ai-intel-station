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

## Daily Discovery

Auto-pilot mode: declare sources in YAML, run on a schedule, get a daily digest. See [docs/daily-discovery.md](docs/daily-discovery.md).

```bash
# One-time setup
uv run research init-config                # writes config/discovery.yaml from template
$EDITOR config/discovery.yaml              # edit repos / searches / categories

# Manual run (no surprise side-effects without --install)
uv run research discover --dry-run                       # see what would happen, **no network** at all
uv run research discover --source github,papers         # run two sources (comma form)
uv run research discover --source papers --source wechat # same, repeated-flag form
uv run research discover --no-briefing                   # collect only, skip the digest

# Read-only inspection (no rerun, no network)
uv run research discover --status                       # last run summary
uv run research discover --log-list 7                   # last 7 runs (one line each)
uv run research briefing --list                         # list generated briefing markdown

# Install macOS launchd schedule (9 AM daily) — choose how hands-on:
uv run research schedule launchd          # print the steps
uv run research schedule launchd --install # actually write + launchctl load
```

Tested offline: the entire `discover` flow (config load → runner → briefing write) is covered
by `tests/test_discovery_config.py` and `tests/test_discovery_runner.py` (19 tests, no
network calls). The CI job `discovery-unit-tests` runs them on every PR.

## Output Layout

```text
output/
  ├─ github/
  ├─ papers/
  ├─ wechat/
  └─ briefing/
```

Raw archives remain source-segregated. Derived reading artifacts are written only under `output/briefing/`.

## L3 Spec Coverage

Each requirement in [`.ai/L3-specs/specs/system.md`](../.ai/L3-specs/specs/system.md) is exercised by at least one real end-to-end test (no business-layer mocking, real subprocess + HTTP where the user-visible flow crosses a process boundary). The full mapping — requirement → test name → test file — lives in **[`docs/l3-coverage.md`](docs/l3-coverage.md)**.

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
