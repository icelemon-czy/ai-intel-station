# WeChat Capability Specification

### Requirement: Normalize Pasted Article URLs
The WeChat ingestion tool SHALL normalize pasted `mp.weixin.qq.com` article URLs before attempting any network fetch.

#### Scenario: Escaped shell separators
- **WHEN** a user pastes a URL containing escaped `\?` or `\&`
- **THEN** the tool converts it to a valid WeChat article URL before fetching

#### Scenario: HTML-escaped separators
- **WHEN** a user pastes a URL containing `&amp;`
- **THEN** the tool decodes it to a valid query string before fetching

### Requirement: Preserve Article Metadata
The generated Markdown SHALL preserve key article metadata.

#### Scenario: Successful article fetch
- **WHEN** the tool fetches an article successfully
- **THEN** the generated Markdown includes at least the article title and source URL

### Requirement: Localize Referenced Images
Images referenced by the article body SHALL be downloaded locally and rewritten to local paths in the generated Markdown when the source content exposes downloadable URLs.

#### Scenario: Article contains downloadable images
- **WHEN** the fetched article body contains supported image URLs
- **THEN** the tool saves them under the article `images/` directory and rewrites Markdown references

### Requirement: Opt-In Live Validation
Live validation of the full WeChat fetch pipeline SHALL remain opt-in.

#### Scenario: No live URLs configured
- **WHEN** `WECHAT_E2E_URLS` is unset
- **THEN** the live e2e test skips cleanly