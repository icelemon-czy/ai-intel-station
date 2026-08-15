# Collection — Archived Delta Spec

## MODIFIED Requirements

### Requirement: Supported Sources

collection SHALL support standalone GitHub repository/search, arXiv category and WeChat article
inputs. Configured daily discovery SHALL additionally support WeChat watchlist, Hacker News feeds and
X recent search. Credential-dependent sources MUST remain optional and MUST NOT couple core startup
to their runtime credentials.

#### Scenario: Choose a collection source

- **WHEN** operator selects a standalone source from `research collect` or a discovery-only source from `research discover --source`
- **THEN**system validates and accepts the source-specific input
- **AND**results write to the corresponding source archive with normalized sidecars

#### Scenario: Start core commands without social credentials

- **WHEN**X is disabled or its credential is absent
- **THEN**non-X collect, query, briefing, status and help actions remain usable
- **AND**no credential is read or transmitted by an unrelated source
