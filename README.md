# AI Intel Station

`ai-intel-station` is a local-first AI intelligence workspace for collecting source material, building a shared library, and generating Obsidian-friendly briefings.

## Agent-First Daily Use

The primary interface is the project Agent + `daily-discovery` Skill. Ask in natural language:

- “今天 AI 圈有什么值得看？”
- “现在跑一遍每日情报，给我 arXiv、GitHub 和 News 重点。”
- “把每日搜索主题改成 agent memory。”
- “昨天为什么失败？”

The Agent operates the deterministic `research` runtime and returns a default composition of five
verified fresh News items (including at least two deduplicated WeChat entries), one GitHub item, and
one arXiv paper. GitHub repositories and arXiv papers retain their evidence role but may lead their
own dedicated lanes; they never fill a missing News slot. Every result includes source and quota
coverage, so a blocked source is not mistaken for a quiet day.
Web remains an optional Library / briefing viewer.

Core setup installs only the project and PyYAML:

```bash
uv sync --frozen
```

Direct WeChat article collection is optional because its browser stack is much heavier. Public-index
watchlist discovery uses the core runtime and does not require a WeChat login:

```bash
uv sync --extra wechat
```

## Business Flow

1. `discover` gathers realtime signals from HN / WeChat / optional X and evidence from GitHub / arXiv
2. `collect` keeps standalone GitHub, arXiv, and direct WeChat article archiving available
3. `query` searches local `ResearchItem` sidecars without re-fetching remote data
4. daily discovery generates coverage-aware signal Markdown; generic `briefing` keeps legacy digest / reading-list output
5. `backfill` rebuilds sidecars from historical Markdown archives
6. `web` optionally serves a local React viewer for dashboard, library browsing, and briefing generation

## Unified Runtime Surface

```bash
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
uv run research collect papers cs.AI --max 10
# One-time before the first WeChat collection: uv sync --extra wechat
uv run research collect wechat "https://mp.weixin.qq.com/s/example"

uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output

# Build the local React workspace, then serve it
npm --prefix web install
npm --prefix web run build
uv run research web
```

## Daily Discovery CLI Reference

The Agent normally performs these actions. The commands remain documented as a deterministic
fallback and automation surface. See [docs/daily-discovery.md](docs/daily-discovery.md).

```bash
# One-time setup
uv run research init-config                # writes config/discovery.yaml from template
uv run research discover --dry-run         # validate config without network

# Manual run (no surprise side-effects without --install)
uv run research discover --dry-run                       # see what would happen, **no network** at all
uv run research discover --source hackernews,wechat     # realtime sources (comma form)
uv run research discover --source hackernews --source x # repeated-flag form; X needs a token
uv run research discover --no-briefing                   # collect only, skip signal briefing

# Read-only inspection (no rerun, no network)
uv run research discover --status                       # last run summary
uv run research discover --log-list 7                   # last 7 runs (one line each)
uv run research briefing --list                         # list generated briefing markdown

# Install macOS launchd schedule (9 AM daily) — choose how hands-on:
uv run research schedule launchd          # print the steps
uv run research schedule launchd --install # actually write + launchctl load
```

Tested offline: the entire `discover` flow (config load → runner → briefing write) is covered
by the broad core suite plus the dedicated `tests.test_discovery_runner` unittest adapter.
CI keeps lightweight core, optional WeChat, and Web validation in separate jobs on every PR.

## Output Layout

```text
output/
  ├─ github/
  ├─ hackernews/
  ├─ papers/
  ├─ wechat/
  ├─ x/
  └─ briefing/
```

Raw archives remain source-segregated. Derived reading artifacts are written only under `output/briefing/`.

## L3 Spec Coverage

Current behavior contracts live under [`.compass/context/L3-specs/specs/`](.compass/context/L3-specs/specs/). The evidence mapping — requirement → code/test anchor → verification status — lives in **[`docs/l3-coverage.md`](docs/l3-coverage.md)**.

## Optional Local Web Workspace

The existing Web workspace is not required for daily discovery. When a visual viewer is useful, it
keeps the same local-first rules as the CLI:

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
