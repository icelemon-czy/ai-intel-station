# GitHub — Delta Spec

## MODIFIED Requirements

### Requirement: GitHub Evidence Role

GitHub repository snapshot 与 search result SHALL 保留 `signal_role=evidence`；缺少该字段的
legacy GitHub item SHALL 也被解释为 evidence。GitHub evidence MUST NOT 独立 seed 或填充
Hacker News / WeChat / X source quota，但 verified fresh GitHub evidence MAY 在 configured
GitHub section 作为 primary reading entry。

#### Scenario: A fresh repository has no social signal

- **WHEN** GitHub repository 有 verifiable recent source activity，但没有 matching realtime signal
- **THEN**它 MAY 以 `low` confidence 占据 dedicated GitHub quota
- **AND**它不消耗 Hacker News / WeChat / X slot，也不声称 social corroboration
