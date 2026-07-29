---
name: skill-creator
description: "创建、更新或精简当前项目的 Skill，明确 trigger boundary、Workflow 和必要 resources，并完成结构与行为验证。Use when the user asks to add, author, revise, rename, merge, split, or validate a project-local Skill; not for installing third-party Skills or ordinary product code changes."
---

# Skill Creator

把用户能够独立表达的目标转化为 concise、可触发、可验证的 project-local Skill。优先更新或合并已有能力；只有现有 Skill 无法自然承载目标时才新增。

## Boundary

- 先找到当前项目的 canonical Skill root；已安装 Compass 时通常是 `.compass/skills/`，维护 Compass source package 时是 `compass/skills/`。
- 默认只修改 project-local Skill。不要写入 global Skill directory、安装 third-party Skill 或发布 package，除非用户明确要求。
- Skill authoring 不走普通 `/develop`；它有独立的 metadata、trigger 和 forward-test contract。
- Skill idea 尚未形成明确用户目标时，先按 [`brainstorm`](../brainstorm/SKILL.md) 收敛，再在同一任务中继续。
- Commit、push 和 release 只有用户明确要求时才执行。

## Flow

### 1. 确认 source of truth

读取最小相关材料：

- root `AGENTS.md` 与 project rule
- canonical Skill inventory
- 最相近的现有 `SKILL.md`
- Skill 所依赖的真实 Workflow、tool、schema 或 domain document

确认是否存在 duplicate Skill root、旧名称或 generated copy。Source of truth 与现有 Skill 冲突时先标记 conflict，不通过复制规则掩盖漂移。

### 2. 定义 trigger contract

在修改文件前明确：

- 用户会怎样表达这个目标
- Skill 必须完成的 observable outcome
- 哪些相邻请求不应触发
- 默认是 read-only 还是允许写入
- 完成后是否需要自然 handoff 到其他 Skill

至少用 concrete positive prompt 和 negative prompt 检查边界；能从上下文确认时不要把这一步变成用户问卷。

### 3. 选择最小 design

依次判断：

1. 这是 Agent 已有的通用能力吗？是则不新增 Skill。
2. 这是现有 Skill 的内部 stage 或 postcondition 吗？是则合并进去。
3. 这是用户可以单独请求、具有独立 input/output 的目标吗？只有此时才保留独立 Skill。

设计 Skill 时：

- 使用 lowercase、digit 和 hyphen；folder name 与 frontmatter `name` 完全一致。
- 优先使用简短、action-oriented name。
- `description` 同时写清做什么、何时触发、何时不触发；不要把 trigger 只藏在 body。
- Frontmatter 只保留当前 repository contract 要求的 field。
- Body 先给 big picture 和 boundary，再给最小 Flow、Output 与 Anti-pattern。
- 只保留 Agent 无法可靠自行推导的 instruction。

### 4. 组织 resources

默认只创建 `SKILL.md`。只有满足以下条件时才增加 resource：

- `scripts/`：需要重复执行、deterministic 且值得实际测试的操作。
- `references/`：详细 domain fact 或 variant 会使主体过重，并且存在明确的按需读取入口。
- `assets/`：Skill 的最终输出需要直接复用的 artifact。

不要创建 Skill-local README、changelog、quick reference、空目录或示例占位文件。不要在 body 和 reference 重复维护同一 fact。

### 5. 创建或更新

- 新建 Skill 时，优先使用环境已有的官方 initializer；不可用时创建最小合法目录和 `SKILL.md`，不要因此安装 dependency。
- 更新 Skill 时保留仍有效的用户规则和 resource，只移除已确认冗余或冲突的内容。
- Rename、merge 或 split 时同步所有 current reference，并移除空的 legacy directory；historical changelog reference 保留原名。
- Public Skill inventory、安装验证和 routing document 存在时，按唯一 source of truth 同步；不要在多个位置复制完整 description。
- 已安装 Compass 时只编辑 `.compass/skills/` canonical source；完成后按 `.compass/INSTALL.md` 重新执行已选 platform installer，将 Skill 更新到各平台的 project-level native directory。不要直接编辑 generated copy。

### 6. 验证

至少检查：

1. `name`、folder 和 allowed character 一致。
2. Frontmatter 可解析，required field 完整，description 包含 positive 与 negative boundary。
3. Body 无 unfinished marker、placeholder、无效 link 或超过 500 行的无必要内容。
4. Relative reference 能从 `SKILL.md` 正确解析。
5. Rename 后没有 current stale reference，Skill inventory count 与 filesystem 一致。
6. 已选 platform 的 Skill copy 与本次 Skill source 一致，或已明确记录内容不同的同名 Skill conflict。
7. `git diff --check` 或等价 whitespace check 通过。

环境提供官方 validator 时先运行。Validator 因 missing dependency 无法启动时，不额外安装 dependency；执行等价结构检查并在结果中如实说明。

### 7. Forward-test

只有 Skill 的 routing、write behavior 或复杂 Workflow 值得独立验证，并且平台允许使用 Subagent 时才 forward-test：

- 使用 fresh context 和真实风格的 positive / negative prompt。
- 只提供 Skill artifact 与任务素材，不泄露预期答案或当前 diagnosis。
- 检查是否正确触发、是否越权写入、是否完成 observable outcome。
- 失败时根据 evidence 修订并重新验证。

简单 metadata rename 或纯措辞调整不强制 forward-test。

## Output

最终报告：

- 创建或更新的 Skill 与 trigger boundary
- 新增或复用的 resource
- routing / inventory 同步
- 实际运行的 validation 与结果
- 未解决的 source-of-truth conflict 或 forward-test limitation

不要把 initializer、validator 或内部 checklist 转交给用户执行。

## Anti-patterns

- 为同一用户目标创建多个相邻 Skill。
- 为内部 Workflow stage 单独创建用户入口。
- 用长篇通用知识填充 Skill，而没有 project-specific procedure。
- 自动创建 scripts、references、assets 或 UI metadata 以显得完整。
- 只验证 YAML，不验证 trigger boundary、stale reference 和实际 write behavior。
- 未经用户要求修改 global environment、commit、push 或 publish。
