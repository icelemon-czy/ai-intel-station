# L5 验证规则

> L5 只记录亲自核实的 evidence。主 Spec 是 behavior source of truth；代码存在、测试文件存在或状态字段为绿色，都不能单独等同于 verified。

## Validation scope

当前主域与 L3 capability 一一对应：

- `system`
- `collection`
- `github`
- `papers`
- `wechat`
- `library`
- `briefing`
- `research-operations`
- `web-workspace`
- `daily-discovery`

旧的 `archive-output`、`research-query`、`research-reporting` 与 `research-web-workspace`
traceability 已分别合并到上述 capability，不再作为独立 truth。

## Status

| Status | Evidence |
|:-------|:---------|
| `verified` | matching implementation + meaningful test assertion 已检查且相关 test 已运行 |
| `partial` | 只覆盖部分 Scenario、部分调用面，或关键 e2e 因环境未运行 |
| `untested` | implementation 已确认，但没有 meaningful test |
| `unimplemented` | Spec 已确认，implementation 未找到 |
| `no-spec` | 重要 user-visible behavior 存在，但主 Spec 未覆盖 |

## Structure checks

对 `system.md` 和每个 capability `spec.md` 检查：

- 每个 `### Requirement:` 至少有一个 `#### Scenario:`
- Scenario 含 observable `WHEN` 与 `THEN`；需要时使用 `AND`
- normative keyword 使用 `SHALL`、`MUST`、`SHOULD` 或 `MAY`
- Requirement 描述 behavior，不绑定 private helper、CSS selector 或 mock 顺序
- `system.md` 覆盖 system boundary 与 cross-cutting behavior
- business Spec 不含 template placeholder、`.ai` runtime path 或重复 Requirement

## Forward traceability

对每个 Scenario：

1. 从 L1 定位 public entrypoint 和真实 call path。
2. 检查 implementation 如何处理 WHEN 并产生 THEN。
3. 阅读 test 的 setup、action、assertion、mock 与 skip。
4. 运行最小相关 command。
5. 在 `traceability/<domain>.md` 记录 concrete file/symbol 与 status。

passing command 不能替代 assertion review；static string assertion 只能证明对应静态 contract。

## Reverse traceability

从 L1 的 public surface 反查 L3：

- `research/cli.py` commands 与 dispatch
- `collect/` validation、failure 与 archive behavior
- `library/` schema、backfill、query 与 resilient loading
- `briefing/` mode、source gap 与 output boundary
- `workspace_web/` API、safe local action 与 job behavior
- `research/discovery/` config、run、log、schedule 与 Web bridge

framework glue、generated bundle 和 trivial utility 不单独创建 Requirement；若它们承载 user-visible contract，则追溯到对应 capability。

## Test gaps and reports

- `partial`、`untested`、`unimplemented` 的 Scenario 才进入 `test-specs/`。
- full sweep 或 change review 写入 `reports/<date>-<scope>.md`。
- report 必须列出实际 command、pass/fail/skip、环境限制与未执行工作。
- socket、network、browser 或 external CLI 不可用时，保留为 limitation，不改写成成功。

## Context migration check

- active agent context 位于 `.compass/context/`
- legacy `.ai/` context tree 已在 user review 后删除；需要审计历史时使用 Git history
- `.agents/skills/` 是 canonical Workflow root；platform directory 只保留必要 thin adapter
- runtime state 不写入 Compass context；daily discovery default 写入 `.state/discovery/`
- legacy `.ai/L4-session/discovery/` 仅在旧 config 显式指定时继续兼容
