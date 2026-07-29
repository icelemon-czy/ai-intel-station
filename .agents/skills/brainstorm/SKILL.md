---
name: brainstorm
description: "通过对话澄清尚未定型的 idea，结合现有 codebase facts 比较 alternatives 并收敛 design direction。Use when the user asks to brainstorm, explore options, shape a vague feature or project, or make a design decision before implementation; not for clear implementation requests, bug fixes, or factual codebase questions."
---

# Brainstorm

把尚未定型的 idea 收敛为用户能够判断的 design direction。先理解现状，再讨论未来；默认只对话，不写 code、Spec、plan、document 或 commit。

## Boundary

- 把本 Skill 作为 `/develop` 或 `/init-project` 的可选前置，而不是 mandatory gate。
- 用户已经明确目标、behavior 和约束时，直接进入对应 implementation Skill，不强制 brainstorm。
- 用户只询问现有 codebase 事实时，使用 `/ask-codebase`，不展开未来 design。
- 只有真正影响 scope、behavior、compatibility、cost 或 risk 的 choice 才交给用户。

## Flow

### 1. 建立 current-state facts

对已有项目，按 [`ask-codebase`](../ask-codebase/SKILL.md) 的只读调查方式获取当前 architecture、code path、constraint、Spec 和 history：

- 只读取与 idea 直接相关的最小 context 和 source。
- 能从 codebase 确认的事实不要询问用户。
- 区分 confirmed fact、reasonable inference 和 product choice。
- 只复用调查证据，不额外输出完整的 codebase Q&A report。

Greenfield idea 没有 codebase facts 时，从用户目标、约束和 success criteria 开始，不虚构现有 architecture。

### 2. 定义 problem

先用简短 big picture 重述：

- 要解决的 user problem
- 已确认的 scope 和 constraint
- 仍会改变 design 的 unknown
- 可观察的 success criteria

如果 idea 包含多个可独立交付的 subsystem，先拆分边界与顺序，只对第一个可决策 scope 继续 brainstorm。

### 3. 澄清 material choice

- 每轮最多询问一个最关键的 product question，避免一次抛出问卷。
- 优先给出 2–3 个互斥 option，说明每个 option 会改变什么；无法合理枚举时再开放提问。
- 没有 material ambiguity 时不要为了完成流程而提问。
- 不把 naming、内部 helper、library preference 等低风险 implementation choice 交给用户。

### 4. 比较 alternatives

只有存在真实 alternatives 时才比较方案：

1. 先给 recommendation 和核心理由。
2. 再说明其他可行方案及 trade-off。
3. 从 user value、complexity、compatibility、operational cost 和 reversibility 中选择当前相关维度。
4. 使用 First Principles Thinking 和 Occam's Razor，删除不服务当前目标的 abstraction 与 feature。

不要为了凑数量制造伪方案。

### 5. 收敛 design direction

从 big picture 到 detail 展开，篇幅随 complexity 调整。只覆盖当前需要的部分：

- goal / non-goal
- user-visible behavior
- system boundary 与主要 component
- data flow、error path 与 compatibility
- risk、验证方式与 anti-overfit test direction

简单 idea 可以用几句话收敛；复杂 design 分段呈现。只在答案会改变下一步时请求确认，不要求逐段 approval。

### 6. 自然 handoff

- 默认在 conversation 中返回 design conclusion，不创建或修改任何 project file。
- 用户明确要求保存时，才写入用户指定的 design artifact；没有指定位置时先询问，不自行新增 document convention。
- 用户确认要创建或更新 Skill 时，直接按 [`skill-creator`](../skill-creator/SKILL.md) 在同一任务中继续。
- 用户确认在已有项目中实施时，直接按 [`develop`](../develop/SKILL.md) 在同一任务中继续，复用已确认 decision，不要求用户再调用 Skill。
- 用户确认创建新项目时，直接按 [`init-project`](../init-project/SKILL.md) 继续。
- 后续 implementation 只有在 observable contract 变化时才创建 L3 change；brainstorm conclusion 本身不自动成为 source of truth。

## Output

先返回一段 design big picture，再按需包含：

- Current facts：影响 design 的 codebase evidence
- Recommendation：推荐方向与理由
- Alternatives：被考虑的其他方案与 trade-off
- Decisions：已确认与仍待确认的 choice
- Validation：怎样判断方向和后续 implementation 正确

不要输出内部 Skill 编排、mandatory checklist 或无关的下一步命令。

## Anti-patterns

- 把 brainstorm 设为所有开发任务的强制前置。
- 询问可以从 codebase 或 source of truth 找到的事实。
- 未经用户要求自动写 Spec、design doc、plan 或 commit。
- 用户只想探索时擅自开始 implementation。
- 方向已确认后，在 handoff 时重复询问相同 decision。
