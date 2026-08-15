# Implementation Tasks

## 1. Tests

- [x] 1.1 default config 使用 `wechat_min_items=0`、`wechat_max_items=2`，并拒绝 min/max/news relation 无效的 config。
- [x] 1.2 News selection 最多渲染 2 个 deduped WeChat contribution，并用 non-WeChat candidate 补足 News quota。
- [x] 1.3 没有 WeChat item 时不产生 quota shortfall；legacy positive minimum 仍产生 shortfall。
- [x] 1.4 WeChat collection failure 在另一个 viable News source 成功时显示为 optional failure 且不单独降低 `ready`。
- [x] 1.5 HN 完成、optional WeChat 失败且零 fresh entry 时为 `no_fresh_signals`。
- [x] 1.6 WeChat 是唯一 attempted News provider 且失败时，nonempty 为 `partial`、zero 为 `coverage_incomplete`。
- [x] 1.7 HN 完成、optional WeChat 失败且 X 同时失败时，HN/X 既有 required attempted-failure 语义使 nonempty 仍为 `partial`。
- [x] 1.8 只有 5 个 WeChat candidate 且 cap=2 时只选 2 条，News missing=3 且 nonempty outcome 为 `partial`。
- [x] 1.9 daily Skill、dry-run composition 与 config example 展示 optional max 2；旧 minimum config 保持兼容。

## 2. Config and Selection

- [x] 2.1 扩展 `BriefingConfig` 与 parser，加入 `wechat_max_items`、bounds、relations 和 legacy migration。
- [x] 2.2 更新 News selection，先满足 optional legacy minimum，再执行 WeChat cap 并保持 deterministic rank。
- [x] 2.3 更新 quota model/Markdown，使 optional cap 不计为 missing quota。

## 3. Coverage and Operator Surfaces

- [x] 3.1 将 optional WeChat failure 与 required coverage failure 分离，同时保留 source failure detail。
- [x] 3.2 更新 runner dry-run、required source dispatch、example/personal config、README/docs 与 daily Skill。
- [x] 3.3 更新现有 Codex automation `ai`，保留 daily 09:00 schedule 和 target task，只替换 prompt。

## 4. Verification and Closeout

- [x] 4.1 运行 targeted tests、core regression 与 dry-run config validation。
- [x] 4.2 完成 SDD verify review、合并 delta、更新 L1/L2/L5 并 archive change。
- [x] 4.3 更新后 read back automation `ai`，直接验证 target task、09:00 schedule、prompt composition 与 honest artifact/failure contract。
