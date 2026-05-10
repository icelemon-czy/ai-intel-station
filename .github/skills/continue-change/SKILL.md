---
name: continue-change
description: "Continue implementing an existing change from changes/. Use when: 继续开发, continue, 接着做, resume change, pick up, 选一个开发, 继续变更, implement change"
argument-hint: "Optional: change name (e.g., 'add-csv-export'). Omit to list all pending changes and pick one."
---

# Continue Change (Resume TDD Execution)

从 `changes/` 中选择一个已有变更，按 TDD 流程继续开发。

> **与 new-change 的区别**：跳过 proposal 和 spec 阶段，从已有的 delta spec / tasks.md 继续。

## Prerequisites

- `.ai/L3-specs/changes/` 下有至少一个变更（不含 `_change-template`）
- 变更已有 proposal.md（状态可为 `drafting` / `implementing` / `review-failed` / `pending-review` / `approved`）

## Procedure

---

### Step 1: 定位变更

**有参数** → 直接读取 `.ai/L3-specs/changes/<name>/proposal.md`，如不存在则报错。

**无参数** → 列出所有未归档变更：

```bash
ls .ai/L3-specs/changes/ | grep -v _change-template
```

对每个变更读取 proposal.md 的 Why + 状态，以及 tasks.md 的完成率，展示：

```
## 可处理的变更

| # | 变更名 | 目的 | 进度 | 状态 |
|---|--------|------|------|------|
| 1 | add-csv-export | 报表支持 CSV 导出 | 2/8 | implementing |
| 2 | fix-login-chars | 登录支持特殊字符 | 0/5 | review-failed |

请选择一个编号继续开发：
```

**等用户选择后继续。**

---

### Step 2: 读取变更上下文

1. 读取 `proposal.md` — Why、What Changes、受影响能力域
2. 读取 `specs/` 下的 delta spec — 所有 Requirement + Scenario
3. 读取 `tasks.md` — 找到下一个未完成的 checkbox
4. 读取 `.ai/L4-session/active-session.md` — 是否有上次中断的进度

#### 2a: L4 漂移检查（必要）

L4 session 内容和实际文件状态可能不一致（上个会话崩了、手工改过代码、git checkout 到其他分支等）。接续前必须交叉验证：

1. active-session.md 声称正在改的文件 → `git status` 此刻有没有相应的 unstaged/staged 改动？
2. tasks.md 已勾选的 checkbox → 对应代码是否真的存在？具体操作：对每个 `✅` 的实现任务，提取关键函数名/文件名，执行 `grep -rn "<函数名>" <src-dir>`，命中 0 行 → 代码不存在，该 checkbox 状态不实
3. 声称测试通过 → 重跑对应的测试确认（只跑当前变更涉及的能力域的测试，非全量）

**任何不一致 → 先把不一致下发给用户，问以哪边为准**，然后更新 L4 和/或 tasks.md，再继续。不得在 L4 没对齐的前提下盲目接着写代码。

---

### Step 3: 判断当前阶段

根据变更内容判断从哪里接续：

| 变更状态 | 操作 |
|---------|------|
| `drafting` | 回到 proposal / spec 准备阶段，补齐后继续 |
| `implementing` | 按 Step 4-8 继续 TDD 执行 |
| `review-failed` | 先读取 Review Feedback，按 Step 7 修复问题，再回到 `pending-review` |
| `pending-review` | 停止继续实现，提示用户先运行 `/review-tests` |
| `approved` | 停止继续实现，提示用户运行 `/archive-change` |

---

### Step 4: 生成 delta spec（如缺失）

与 new-change Step 4 相同：

为每个受影响的能力域创建 `changes/<name>/specs/<capability>/spec.md`：

| 情况 | delta spec 区段 |
|------|----------------|
| 全新能力域 | `## ADDED Requirements` |
| 修改已有能力域 | `## MODIFIED Requirements` |
| 删除需求 | `## REMOVED Requirements` |

**每个 Requirement 至少 1 个 Scenario**，使用 WHEN/THEN 格式。

### Step 5: 生成 tasks.md（如缺失）

与 new-change Step 5 相同：

参考 `.ai/L3-specs/changes/_change-template/tasks.md`：

- **第一组固定为 Tests** — 从 Scenario 的 WHEN/THEN 直接映射为测试用例
- 后续组为实现步骤，按依赖排序
- checkbox 格式：`- [ ] X.Y 描述`

### Step 6: 从 Scenario 写测试代码

读取 `.ai/L2-rules/testing.md`（如存在）— 遵守项目测试规范。

对 delta spec 中**尚未有测试的** Scenario，写测试：

- **WHEN** → 测试的 setup + action
- **THEN** → 测试的 assertion
- 覆盖：happy path + edge case + error path

**运行测试，确认新写的测试失败（红灯）。**

勾选 tasks.md 中 Tests 组的对应 checkbox。

### Step 7: 实现代码

让测试通过：

1. 读取 `.ai/L2-rules/global.md` + 相关模块规则 — 遵守编码约束
2. 跨模块修改 → 先查 `.ai/L1-codebase-map/module-map.md` 变更联动表
3. 创建新文件 → 查 `.ai/L2-rules/templates.md`
4. 实现代码
5. **运行测试，确认全部通过（绿灯）**

勾选 tasks.md 中对应实现步骤的 checkbox。

### Step 8: 收尾

1. 更新 `.ai/L5-validation/traceability/<domain>.md` — 新增/修改的 Scenario 标为 ✅ verified
2. proposal.md 状态改为 `pending-review`
3. tasks.md 所有 checkbox 勾选完毕
4. 更新 `.ai/L4-session/active-session.md` — 记录完成内容和测试结果

---

### 输出格式

接续时展示：

```
## 继续开发: <change-name>

**目的**: [Why，一句话]
**当前进度**: tasks X/Y 完成
**接续点**: [Step N — 具体描述]

### 待完成任务
- [ ] [下一个未完成的 checkbox]
- [ ] ...

开始执行。
```
