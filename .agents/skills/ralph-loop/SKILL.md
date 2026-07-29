---
name: ralph-loop
description: "对有客观完成条件的任务持续迭代，直到验证通过或出现真实阻塞。Use only when the user explicitly asks for Ralph Loop, persistent iteration, or not to stop until checks pass."
---

# Ralph Loop — 持续迭代直到可验证终点

把一个明确任务变成外层循环：读取当前证据，执行一轮最小有效改进，重新验证，然后在未达到终点时继续。优先使用平台已经提供的持久 goal/continuation 能力；不要为了本 Skill 安装 Stop hook、复制 Skill 或在仓库中创建循环状态文件。

## Loop contract

开始前提取并明确：

1. **Objective**：最终要实现什么。
2. **Completion criteria**：哪些客观事实同时成立才算完成。
3. **Verifier**：实际运行什么测试、构建、lint、类型检查、基准或 eval。
4. **Scope**：允许修改和禁止触碰的范围。
5. **Safety cap**：可选的最大轮次、token budget 或完成承诺；用户没有提供时不要虚构。

优先从项目真实配置、`.compass/context/L2-rules/testing.md` 和现有 eval 中发现验证命令，不要猜测。能够安全推断时直接开始；缺失选择会实质改变结果，或完全没有诚实的完成判据时，只问一个阻塞问题。

开放式 idea exploration 没有客观 Completion criteria，不启动 Ralph Loop；改用 `/brainstorm` 与用户收敛 design direction。

## Start persistent execution

显式调用 `/ralph-loop`、`$ralph-loop` 或明确要求 Ralph Loop，表示用户授权为该任务启动持久执行。

1. 平台已有 goal 工具时，先检查当前 goal：
   - 同一目标未完成：继续现有 goal；
   - 不同目标未完成：不要覆盖，报告冲突并请用户先完成或清除；
   - 没有未完成 goal：创建包含 Objective、Completion criteria、Verifier、Scope 和停止条件的 goal。
2. 只有用户明确提供 token budget 时才设置 token budget。
3. 平台没有持久 goal/continuation 能力时，在当前运行中执行同一循环，并明确说明无法保证跨 turn 自动续跑。
4. 不修改平台配置，不安装 hook，不创建第二份 Skill 来增强持续性。

用户指定最大轮次时，把目标定义为“最多执行 N 轮”。达到上限但底层任务未完成时，循环本身可以结束，但必须把底层任务报告为 incomplete，不能伪装成成功。

## Iteration cycle

每轮只做一个有证据支持的最小推进：

1. **Measure**：运行最小且最相关的 verifier，记录当前失败或分数基线。
2. **Choose**：选一个失败、瓶颈或新诊断假设作为本轮目标。
3. **Route**：需要现有 Compass 工作流时，每轮只调用一个最匹配的 Skill：
   - 单个 bug 或测试失败 → `/fix-bug`；
   - 开发功能、调整行为、重构，或继续已有计划内变更 → `/develop`；
   - 创建、更新或验证 project-local Skill → `/skill-creator`；
   - 测试可信度专项审计 → `/audit-tests`；
   - 只需定位或影响分析 → `/ask-codebase`。
4. **Act**：在授权范围内实现或诊断。
5. **Verify**：每次有意义的改动后重新运行相关 verifier，并直接检查输出或生成物。
6. **Decide**：
   - 所有完成条件均成立 → 进入完成流程；
   - 仍失败且存在新的可行假设 → 开始下一轮；
   - 到达人工门槛、权限边界或外部依赖 → 按阻塞规则处理。

有限轮次存在时，在 plan 或进度更新中保留紧凑的 `Iteration X/N`；不要仅为计数写入仓库文件。

## Integrity rules

- 不删除、跳过、弱化或改写正确测试来制造绿灯；测试确实错误时，必须先给出 Spec 与失败证据。
- 不用未运行、过期、局部或不可复现的结果宣称完成。
- 不重复完全相同的失败动作；下一轮必须有新假设、新证据或不同策略。
- 不因循环持续执行而扩大权限、修改范围、外部副作用或生产访问。
- 不绕过 `/develop` 的必要业务决策、SDD review、测试证据或权限边界。
- 不输出 completion promise，除非与它绑定的全部条件真实成立。
- 先跑最小相关检查，再跑完成契约要求的完整回归验证。

## Stop conditions

### Success

仅当所有 Completion criteria 成立、所需 verifier 已实际成功运行且没有剩余必做项时宣布成功。平台有 goal 完成工具时，此时才标记 goal complete，并报告具体证据。

用户提供精确 completion promise 时，只在成功报告最末尾输出一次。

### Finite-cap exit

达到最大轮次但底层任务仍未完成时，报告：

- 已完成内容；
- 仍失败内容；
- 最新 verifier 证据；
- 最佳下一假设；
- `Ralph loop finished; underlying task incomplete.`

### Blocked

只有真正缺少外部依赖、必要权限或用户业务决策，并且已经穷尽安全替代路径时才报告阻塞。平台对持久 goal 有更严格的 blocked 判定规则时，以平台规则为准。困难、耗时、分数不够高或一次尝试失败都不构成阻塞。
