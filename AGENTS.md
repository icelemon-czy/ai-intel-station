# AGENTS.md

## Working order

1. 读取 [README.md](README.md)，确认 project purpose、Document map 与 operator entry。
2. 读取 [system design](doc/system_design.md)，确认改动所属 layer；再读取相关 `doc/*_design.md`。
3. 以用户确认和已有 design 判断 intended behavior；code、config、test 与 runtime evidence 只证明 current implementation。
4. 如果 intended behavior 与 current implementation 冲突，先标记 conflict 并向 user 说明，不从 code 反推需求。

## Request routing

| Request | Canonical playbook |
|:--------|:-------------------|
| `/brainstorm`、`/build-docs`、`/maintain-docs` | `.cursor/skills/<name>/SKILL.md` |
| `/ralph-loop`、`/skill-creator` | `.cursor/skills/<name>/SKILL.md` |
| Daily intelligence | `.agents/skills/daily-discovery/SKILL.md` |
| 无关的一次性 source fetch | `.agents/playbooks/wechat/SKILL.md`、`.agents/playbooks/github/SKILL.md` 或 `.agents/playbooks/papers/SKILL.md` |

明确调用或语义命中 Workflow 时，完整读取对应 `SKILL.md`。所有 product operation 通过唯一 `research` CLI 执行；不要恢复旧 context hierarchy、platform-specific full Skill copy 或 standalone source entrypoint。

## Documentation rules

维护 agent-facing document 时，动词使用中文，核心名词使用 English。所有 document 先说明 big picture 和主线 flow，再展开 detail。

- `README.md` 只维护 project purpose、Document map 和必要 operator entry；feature detail 放入 `doc/<feature>_design.md`。
- `doc/todo.md` 只在确实需要 current work list 时维护，不保存永久 design 或已完成历史。
- 按独立目的、observable behavior 和 ownership 判断 feature boundary，不按源码目录机械拆分；同一 flow 的内部 layer 留在同一份 design。
- overview 只凸显目的和数据流；optional parameter、path 和 field-level detail 放入对应 detail document。
- 同一 fact 只维护一处，其余位置引用 canonical document。
- 新增、rename、split、merge 或删除 feature 时同步 README Document map；behavior、boundary、flow、dependency 或重要 decision 改变时同步对应 design。
- 不改变 design fact 的内部修改不制造 document churn。

## Engineering rules

### Design 与 implementation

- 从基本事实、约束和目标推导 design；如无必要，不增加 abstraction、entity、schema、dependency 或 layer。
- 先确认 source of truth，再开始 implementation。
- 不修改 source of truth 或 design artifact，除非 user 明确要求，或本次改动已经改变对应 behavior。
- 保持现有 code structure、design style 和 layer boundary；优先沿用已有 module、helper 与 pattern。
- 把可变环境、path、selector、timeout、feature flag 和 prompt parameter 放入已有 config boundary。

### Testing

- 先读取相关 source of truth 和 canonical test command（优先 README / design，其次 project config）。
- 测试 behavior 和 user-visible contract，避免 overfit implementation detail。
- 不把 test 绑定到 brittle selector、临时 copy、内部 helper 调用顺序、mock 的无关 field 或当前 bug。
- 使用最小必要 fixture 和 assertion；每个 assertion 对应真实 requirement、risk 或 regression。
- source of truth 与 implementation 冲突时，只固化已确认 behavior。

## Review output

Review 先从 high-level requirement 和 source of truth 判断 implementation / test 是否 overfit 当前 case，并检查 missing anti-overfit test。每个问题按以下顺序说明：

1. **问题**：指出 defect、risk、regression、overfit 或 missing test，并引用 file/line。
2. **白话解释**：说明上下文及其对 user 或 maintainer 的影响。
3. **当前状态**：说明 implementation、已有 test 与缺口。
4. **解决方案**：给出最小修复；必要时补充从 high-level requirement 推导的 anti-overfit test。

<!-- compass:start -->
## Language Style

维护任何 agent-facing document 时，动词使用中文，核心名词使用 English。

## Documentation Style

维护任何 document 时逐层递进：先给 big picture（目标和主线 flow），再展开细节。

- 项目自己的 `README.md` 只维护项目目的、Document map 和必要入口；feature design 放在 `doc/<feature>_design.md`；`doc/todo.md` 只在需要时维护当前工作，不保存永久 design。
- Feature boundary 按独立目的、observable behavior 和 ownership 判断，不按源码目录机械拆分；同一 flow 的内部 layer 留在同一份 design。
- overview 层（开头段落、table、diagram）凸显目的和数据流，不堆 optional 参数、路径或 field-level 细节；细节放到对应展开层或 referenced document。
- 分层放置：entry document 放主体和导航，detail document 放展开。
- 同一 fact 只维护一处，其余位置用引用指向，避免多处 copy 漂移。
- 用户确认和已有产品文档决定 intended behavior；code、config、test 与 runtime evidence 证明 current implementation。发生冲突时标记 conflict，不把当前实现自动写成产品需求。
- 新增、rename、split、merge 或删除 feature 时同步 README Document map；behavior、boundary、flow、dependency 或重要 decision 改变时同步对应 design；不改变 design fact 的内部修改不制造 document churn。

## Developing Principles

### Design

- First Principles Thinking：从最基础的事实、约束和目标出发重新推导 design。
- Occam's Razor：如无必要，勿增 abstraction、entity、schema、dependency 或 layer。

### Implementation

- 先确认 source of truth，再开始 implementation；当 source of truth 与 implementation 冲突时，先标记 conflict 并向 user 说明。
- 不要修改 source of truth 或 design artifact，除非 user 明确要求，或本次改动已经改变了对应行为。
- 保持现有 code structure、design style 和 layer boundary；优先沿用已有 module、helper、pattern，不为了局部便利新增 layer。
- 抽离 code 中的 config：将可变环境、路径、selector、timeout、feature flag、prompt 参数等放到已有 config boundary。

### CLI Worker Delegation

项目启用 Compass CLI worker 时，planner 不按 Write / Edit / Bash 的 tool-call 粒度调用 Claude：

1. implementation 开始前，将一个完整且 bounded 的 task 写入 `.compass/context/cli-worker-task.md`，包含原始 goal、已确认 scope、acceptance criteria、明确的 out-of-scope 和一行 `model: sonnet` 或 `model: opus` 分类：
   - `model: sonnet`：confirmed-scope 的常规 implementation（edit、delete、probe、沿用现有 pattern 的小 feature、docs、tests）。
   - `model: opus`：需要更深 reasoning 的 task（未决定的 architecture、大型 multi-module change、未确认 root cause 的 hard bug、security-sensitive change）。
   不要把每个 task 默认写成 opus；省略 `model:` 时 worker 按 `sonnet` 执行。
2. 按 hook 返回的 platform command 只执行一次 `--delegate`。不要直接执行 raw `claude` command，不要使用 `--resume`、`--continue`、`--session-id`，也不要把同一 task 拆成逐文件 delegation。
3. worker 返回后检查 diff 并做独立 verification。相同 task revision 不重复执行；只有 scope 或 acceptance criteria 确实改变时才重写 task spec。
4. worker 报 blocker 时停止，不通过扩大 scope 或连续生成新 task revision 绕过 blocker。

### Testing

生成或修订 test 时：

- 先读取相关 source of truth 和测试命令（优先 README / design，其次项目配置）。
- 测试 behavior 和 user-visible contract，避免 overfit implementation detail。
- 避免把 test 绑定到 brittle selector、临时 copy、内部 helper 调用顺序、mock 的无关字段或当前代码的 bug。
- 使用最小必要 fixture 和 assertion；每个 assertion 都应对应真实 requirement、risk 或 regression。
- 当 source of truth 与 implementation 冲突时，只在 test 中固化已确认 behavior。

## Review Rule

进行 review 时，先从 high-level requirement 和 source of truth 判断 implementation / test 是否 overfit 当前 case，并检查是否缺少 anti-overfit test。

每个问题按以下结构返回：

- 问题：指出具体 defect、risk、regression、overfit implementation、overfit test 或 missing anti-overfit test，并引用 file/line。
- 白话解释：说明问题上下文、为什么会影响 user 或维护者。
- 当前状态：说明代码现在怎么做、test 现在覆盖了什么、缺口在哪里。
- 解决方案：给出最小可行修复；必要时补充从 high-level requirement 出发的 anti-overfit test，避免只绑定当前 fixture、mock、copy、selector 或 implementation detail。

<!-- compass:end -->
