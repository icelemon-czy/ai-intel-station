# Papers — Delta Spec

## MODIFIED Requirements

### Requirement: Papers Evidence Role

Paper SHALL 保留 `signal_role=evidence`；缺少该字段的 legacy Paper SHALL 也被解释为 evidence。
Paper evidence MUST NOT 独立 seed 或填充 Hacker News / WeChat / X source quota，但 verified
fresh Paper MAY 在 configured arXiv section 作为 primary reading entry。

#### Scenario: A fresh Paper has no social signal

- **WHEN** Paper 有 verifiable recent `published_at`，但没有 matching realtime signal
- **THEN**它 MAY 以 `low` confidence 占据 dedicated arXiv quota
- **AND**它不消耗 Hacker News / WeChat / X slot，也不声称 social corroboration
