# WeChat — Archived Delta Spec

## ADDED Requirements

### Requirement: Account Watchlist Discovery

WeChat daily discovery SHALL accept configured public-account watchlist entries and perform
best-effort discovery through a declared public-index adapter, independently from full article URL
collection.

#### Scenario: Discover a watchlist article

- **WHEN**a configured account index returns an article with title, link and publication timestamp
- **THEN**system saves a lightweight `source=wechat`, `signal_role=signal` ResearchItem
- **AND**the item identifies its account, discovery method and watchlist membership

### Requirement: Honest WeChat Discovery Coverage

Public-index CAPTCHA, access block, empty malformed page or missing publication metadata MUST be
reported as incomplete coverage; the system MUST NOT claim complete account history or silently
interpret the failure as no new article.

#### Scenario: Public index requires verification

- **WHEN**the WeChat watchlist adapter detects a CAPTCHA or abnormal-access response
- **THEN**WeChat source reports failure with a readable reason
- **AND**other source collection and briefing continue

#### Scenario: Public index response is empty, malformed or lacks publication time

- **WHEN**the adapter receives a nominally successful page that has no attributable result, cannot be parsed, or omits publication time
- **THEN**WeChat source reports incomplete coverage with the precise reason
- **AND**the response is not saved as a verified fresh signal or counted as a quiet account
