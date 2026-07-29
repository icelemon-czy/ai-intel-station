# WeChat Collection — Delta Spec

> 本文件描述对 `specs/wechat/spec.md` 的增量变更。
> 已于 2026-07-25 合并到 main Spec，保留为 archive evidence。

## MODIFIED Requirements

### Requirement: Explicit Runtime Failure

缺失 optional WeChat runtime、缺失 browser runtime、无效 URL 或 fetch failure MUST 返回
明确失败；缺失 optional dependency 时 guidance MUST 指向 `wechat` install extra，且 CLI
MUST NOT 输出未处理的 Python traceback。

#### Scenario: Article cannot be fetched

- **WHEN** URL 无效或 browser fetch 失败
- **THEN**当前 collection 返回可读错误
- **AND**不生成伪成功 sidecar

#### Scenario: WeChat extra is not installed

- **WHEN**operator 在 core-only environment 运行 WeChat collection
- **THEN**command 返回 non-success status 与 `uv sync --extra wechat` guidance
- **AND**GitHub、Papers、query、briefing 与 discovery control action 仍可使用
