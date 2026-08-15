# Implementation Tasks

## 1. Tests

- [x] 1.1 新增 ranked pool test：多个高排名 GitHub destination 被 cap 为 1，并由 non-GitHub candidate 补满。
- [x] 1.2 新增 replacement 不足 test：不绕过 cap，News missing 与 `partial` 可观察。
- [x] 1.3 新增 cross-lane test：dedicated duplicate 不占 News GitHub slot，distinct GitHub signal 可进入。
- [x] 1.4 新增 config test：default/custom/bounds、legacy compatibility 与 example parity。
- [x] 1.5 新增 renderer test：title 链 original GitHub target，HN attribution 链 discussion URL；missing metadata fallback；X/WeChat attribution 保持 canonical。
- [x] 1.6 新增 host decision table：exact/subdomain GitHub、github.io、lookalike 与恶意 suffix。
- [x] 1.7 新增 mixed WeChat/GitHub dual-cap tests：有 replacement 仅 WeChat short；无 replacement 同时 News short。
- [x] 1.8 新增 cap=0 tests：zero total entry 为 no_fresh；有 dedicated entry 为 partial。
- [x] 1.9 新增 config migration：old quota default、pure legacy uncapped、mixed reject、digest ignore、无 GitHub source requirement。
- [x] 1.10 exact excluded count 覆盖 greedy skip、cross-lane duplicate 与 cutoff 后 candidate；Markdown 精确展示 actual=1/max=1/excluded=2。
- [x] 1.11 dry-run assertion 只展示 configured maximum，actual/excluded 为 unavailable。

## 2. Selection and Rendering

- [x] 2.1 在 quota selector 增加 normalized GitHub destination predicate 与 post-dedupe cap/replacement。
- [x] 2.2 传递 `github_news_max_items` config；legacy mode 不启用 cap。
- [x] 2.3 renderer 使用 source-native attribution URL，保持 title/dedupe identity 不变。
- [x] 2.4 artifact 与 dry-run composition 展示 GitHub News actual/max/excluded。

## 3. Verification and Closeout

- [x] 3.1 跑 targeted selection/config/runner tests 与 core regression。
- [x] 3.2 用当前 local signal archive 生成 deterministic briefing，确认 News 中 GitHub destination ≤1。
- [x] 3.3 完成 SDD verify、Spec merge、L1/L2/L5 sync 与 archive。
