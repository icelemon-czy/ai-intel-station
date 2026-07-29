# [Domain Name] 测试用例设计

> 对应 spec: `.compass/context/L3-specs/specs/<domain>/spec.md`
> 对应追溯: `.compass/context/L5-validation/traceability/<domain>.md`
>
> 本文件为 traceability 表中 ⚠️ untested / ⚠️ partial / ❌ unimplemented 的 Scenario 设计具体测试用例。
> 已有测试且状态为 ✅ verified 的 Scenario 不需要在此文件中出现。

## Requirement: [Name]

### Scenario: [Name]

> 来源: L3 spec 的 WHEN/THEN 描述

| Case | 类型 | Input | Expected | 备注 |
|------|------|-------|----------|------|
| [正常情况描述] | happy path | [具体输入数据] | [具体预期输出] | |
| [边界情况描述] | edge case | [具体输入数据] | [具体预期输出] | |
| [异常情况描述] | error path | [具体输入数据] | [具体预期输出/错误信息] | |

**Setup**: [测试前置条件，如需要的数据库状态、mock 配置等]

**Teardown**: [测试清理操作，如有]
