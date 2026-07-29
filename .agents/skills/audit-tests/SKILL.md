---
name: audit-tests
description: "深度审计现有测试是否覆盖预期行为、调用真实代码并能捕获回归。Use when the user explicitly asks to assess test quality, coverage, assertions, mocks, skips, or false passes; not for ordinary code review or fixing a known bug."
---

# Audit Tests

对已有测试或能力域做独立可信度审计。正常 `/develop` 已自动执行必要的代码与测试 review；不要要求完成计划内开发的用户再调用本 Skill。

## Ownership

- Main Agent 选择范围、运行测试、组织 findings 并核实最终证据。
- `sdd-reviewer` 以 `mode=verify` 做只读独立检查。
- 角色不可用时，Main Agent 按同一协议完成，不要求用户安装或运行其他入口。
- 本 Skill 不是普通 code review；它只判断测试是否真实保护预期行为。
- 默认只返回 findings 和 verdict，不修改代码、Compass context、变更状态或审计报告。
- 用户明确要求保存报告时才写入用户指定位置；用户未指定位置时使用 `.compass/context/L5-validation/reports/audit-<target>-<YYYYMMDD>.md`。
- 用户同时要求修复已确认的问题时，转为 `fix-bug`；其他计划内代码修改转为 `develop`。

## Procedure

1. 明确一个审计目标：用户指定的 change、能力域、测试目录或文件；范围模糊时选择与问题直接相关的最小范围。
2. 读取 `.compass/context/L2-rules/testing.md` 和 `.compass/context/L5-validation/validation-rules.md`。若 testing.md 缺失，从真实配置、脚本和测试文件发现命令与约定，在审计结果中标记 context gap，不提示 setup Skill。
3. 枚举范围内所有 Requirement / Scenario；独立测试集没有 Spec 时，枚举被声称保护的生产行为并明确标为无 Spec 基线。
4. Main Agent 运行最小相关测试，记录命令、退出状态、失败和 skip/only/pending 标记。
5. 以 `mode=verify` 委派 `sdd-reviewer`，提供目标、实际测试输出和相关 diff；要求按 validation-rules 返回逐 Scenario 证据及 `PASS` / `BLOCKED`。
6. Main Agent 打开关键测试和生产路径复核 Subagent 引用，不能把绿色输出或 traceability 标签当成证明。
7. 直接组装审计结果，包含：
   - 测试命令和实际结果
   - Scenario → assertion → production call path
   - weak assertion、mock、skip、missing boundary 和 false-pass findings
   - 覆盖限制与未验证项
   - 最终 verdict
8. 直接向用户报告审计结论。只有用户明确要求保存报告时才落盘；不要提示用户再运行内部 closeout、context sync 或 commit Workflow。

## Verdict

- `PASS`：每个范围内 Scenario 都有对齐 THEN 的具体 assertion、真实生产调用和实际通过证据，且无阻塞反模式。
- `BLOCKED`：存在缺失测试、弱/错位 assertion、mock 被测主体、异常跳过、调用链未触达、失败测试或关键证据缺失。

不设置“有警告也自动通过”的模糊中间态。非阻塞观察项单独记录，但不能掩盖任何 blocking finding。
