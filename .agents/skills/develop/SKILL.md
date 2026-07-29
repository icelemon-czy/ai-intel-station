---
name: develop
description: "开发功能、调整行为或重构代码，并自动完成必要的规划、测试、review、context sync 和收尾。Use for clear planned work in an existing project; not for authoring Skills, open-ended brainstorming, bug diagnosis, new-project setup, read-only questions, or standalone test audits."
---

# Develop

把一次代码变更从用户目标推进到可验证交付。用户不需要编排 proposal、review、archive 或 context sync；这些都是本 Workflow 的内部阶段。

## Ownership

- Main Agent 是唯一 writer、状态机 owner 和最终 verifier。
- `sdd-reviewer` 只读返回证据，不修改代码、Spec、报告或状态。
- 平台没有该角色、角色冲突或调用失败时，Main Agent 直接按同一规则完成检查，不要求用户补运行另一个 Skill。
- Commit 和 push 不属于本 Workflow；只有用户明确要求时才执行。

## Route by intent and state

1. 读取最小相关 L1/L2、`.compass/context/L3-specs/change-management.md` 和现有 `changes/`。
2. 用户指定已有 change 或明确说继续时，恢复该 change；不要新建重复 proposal。
3. 用户明确要求关闭或归档时，从当前状态继续验证，只有通过后才归档。
4. 用户只是询问状态时，按 `ask-codebase` 的 change-status 模式只读回答。
5. 用户要创建、更新、rename、merge 或验证 Skill 时，转入 `skill-creator`，不按普通 product change 处理。
6. 用户明确说“先想想”、比较方案，或目标尚未形成可判断的 behavior 时，先按 `brainstorm` 收敛 design；不要创建 change 或开始 implementation。用户随后确认实施时，在同一任务中继续并复用已确认 decision。
7. 其他新工作直接判断是否需要 SDD：

| 变化 | 路径 |
|:-----|:-----|
| 可观察行为、业务规则、API、schema、权限、兼容性变化 | SDD |
| 内部重构、机械迁移、文档或配置调整，且不改变外部契约 | Lightweight |
| 行为异常、测试失败、review 打回 | `fix-bug` |

不要为了流程完整而创建无业务价值的 Spec entity。无法确定是否改变契约时，先查源码、调用者和现有 Spec；只有答案会改变产品行为时才问用户。

## SDD path

### 1. Draft the change

按 `change-management.md` 创建或补齐 `changes/<name>/`：

- `proposal.md`：Why、What Changes、影响和真正的备选决策。
- `specs/<capability>/spec.md`：只记录行为契约的 ADDED / MODIFIED / REMOVED Requirement。
- `tasks.md`：Scenario 测试在前，实现任务在后。

只有存在会实质改变范围、兼容性、数据迁移或业务行为的歧义时，合并成一批问题向用户确认。精确请求、可从代码确认的事实和低风险实现选择不形成用户门槛。

### 2. Run the plan review

当 `sdd-reviewer` 可用时，以 `mode=plan` 委派，要求读取实际 proposal、delta spec、相关主 Spec 和代码证据。Main Agent 复核返回的文件与符号后：

- 技术性遗漏直接修正。
- 业务歧义才询问用户。
- 无阻塞项后把状态推进到 `implementing`。

### 3. Execute TDD

1. 读取真实的测试命令和 `.compass/context/L2-rules/testing.md`；缺失或过期时，从项目配置和测试中自动校正最小规则，不提示用户运行 setup Skill。
2. 将每个 Scenario 的 WHEN 映射为 setup/action，将 THEN 映射为具体 assertion。
3. 先运行新增测试并观察预期红灯；若行为已存在，核对 Spec 和范围，不能伪造红灯。
4. 写代码前读取 `global.md`、`testing.md` 和受影响模块规则。
5. 实现最小代码，运行相关测试至绿灯。
6. 对本次使用的 L2 规则逐条检查；不符合先修复。
7. 相关测试绿灯且 L2 检查完成后，将状态从 `implementing` 推进到 `pending-review`，并在 proposal 的 append-only 日志中记录证据摘要。恢复时已是 `pending-review` 则不重复写转移。

### 4. Review and repair internally

仅在状态为 `pending-review` 时执行本步。读取 `.compass/context/L5-validation/validation-rules.md`，由 Main Agent 运行相关测试并保存原始结果，再以 `mode=verify` 委派 `sdd-reviewer`；Subagent 只做只读审查。

- `PASS`：Main Agent 核实关键证据后，将状态从 `pending-review` 推进到 `approved`，并记录转移证据，再继续 closeout。
- `BLOCKED`：先将 `pending-review` 推进到 `review-failed`，记录 finding 和证据。代码/测试问题在开始修复时再将 `review-failed` 推进到 `implementing`；修复后重新运行测试与 L2 检查，再进入 `pending-review`。不要把下一条命令交给用户。
- Spec 与期望冲突：保持 `review-failed` 并只在需要业务决策时暂停；用户决策后先进入 `implementing` 落实 Spec/测试修正，再重走绿灯与 review。
- 平台无 Subagent：Main Agent 按 validation-rules 的同一协议完成 review。

不得因为合并了入口而弱化 Scenario 覆盖、真实调用链、mock、skip、弱 assertion 或 false-pass 检查。

### 5. Close out automatically

仅在状态为 `approved`、相关测试通过、review 为 `PASS` 且无未解决业务歧义时：

1. 按 `.compass/context/doc-sync.md` 自动同步实际 diff 命中的 L1/L2。
2. 更新 L5；只有亲自核实的 Scenario 才标记 `verified`。
3. 将 delta spec 合并到主 Spec：ADDED 追加、MODIFIED 整块替换、REMOVED 删除。
4. 验证 Requirement/Scenario 结构、重复项和追溯一致性。
5. 将 `changes/<name>/` 移动到 `archive/<name>/`，将状态从 `approved` 推进到 `archived` 并记录转移证据，然后清理 L4 指针。

归档是成功 change 的内部后置条件，不再要求用户确认或运行另一个 Skill。若用户明确要求仅实现、不归档，则尊重该范围并报告停留状态。

## Lightweight path

不创建 proposal 或 delta spec。直接：

1. 读取相关 L1/L2 和实际验证命令。
2. 实施最小变更并运行相关检查。
3. 对行为未改变这一假设做 diff 和调用面复核；发现契约变化立即升级到 SDD path。
4. 按 `doc-sync.md` 自动同步 L1/L2，并报告证据。

## Resume rules

恢复已有 change 时，以实际文件和 Git 状态为准：

- `drafting`：补齐 plan review 和必要业务决策。
- `implementing`：从第一个未完成且能由源码验证的任务继续。
- `pending-review` / `review-failed`：自动进入 review-repair loop。
- `approved`：验证前置证据后自动归档。
- L4、tasks 和源码不一致时，先用 Git、代码和测试校正事实；只有多种恢复方式会丢失用户工作时才询问。

## Output

最终只向用户报告：完成目标、关键代码变化、测试与 review 证据、context 同步、归档状态和仍需决策的事项。不要输出一串后续 Skill 命令。
