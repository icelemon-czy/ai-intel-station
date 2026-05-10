---
name: new-change
description: "Create a new change proposal with spec-driven TDD workflow: proposal → confirm → delta spec → tests → implement. Use when: 新需求, new feature, 加功能, add feature, 改需求, change request, 新变更, create change, 我要做, implement"
argument-hint: "Describe what you want to change or add (e.g., 'add CSV export for reports', '添加用户头像功能')"
---

# New Change (Spec-Driven TDD)

按 spec-driven TDD 流程创建新变更：proposal → 人确认 → delta spec → 写测试（红）→ 实现代码（绿）→ 完成。

> **核心纪律**：人只确认一次（proposal 阶段）。确认后 AI 全自动：生成 spec → 先写测试 → 再写代码 → 测试通过即完成。

## Prerequisites

- `.ai/` 目录已存在且有 L1 + L3 + L5 结构
- 用户描述了要做的变更（新功能 / 需求变更 / 重构等）

## Procedure

---

### Phase A: 设计（需人确认）

#### Step 1: 收集上下文

1. 读取 `.ai/L1-codebase-map/overview.md` — 项目功能索引
2. 读取 `.ai/L3-specs/specs/system.md` — 系统级需求

```bash
# 已有能力域
ls .ai/L3-specs/specs/ | grep -v _capability-template | grep -v system.md

# 进行中的变更（避免冲突）
ls .ai/L3-specs/changes/ | grep -v _change-template
```

3. 根据变更描述，定位涉及的功能和模块：
   - `.ai/L1-codebase-map/features/[name]/README.md`
   - `.ai/L2-rules/[module].md`
   - `.ai/L3-specs/specs/<domain>/spec.md`（如已存在）

#### Step 2: 创建 proposal.md

用 kebab-case 命名变更，如 `add-csv-export`、`fix-login-special-chars`。

创建变更目录：

```
.ai/L3-specs/changes/<name>/
├── proposal.md
├── specs/         (delta specs, Step 4 生成)
└── tasks.md       (Step 5 生成)
```

参考 `.ai/L3-specs/changes/_change-template/proposal.md`，填写：

- **Why**: 为什么做、为什么是现在（1-2 句话）
- **What Changes**: 具体变更列表，标注破坏性变更为 **BREAKING**
- **Alternatives Considered**: 备选方案及选择理由
- **Capabilities Affected**: 新增/修改的能力域
- **Impact**: 影响范围

状态设为 `implementing`。

#### Step 3: 展示 proposal + 业务问题 → 等人确认

向用户展示 proposal 摘要，**同时**提出 3-5 个需要确认的业务问题。

**问题必须来自以下 6 个维度**（逐维度检查，跳过无关维度，但必须在输出中标注"不适用"）：

| 维度 | 示例问题 |
|:-----|:---------|
| 范围边界 | "这个功能只对 admin 还是所有用户？" |
| 边界/极端情况 | "超过 10 万条时分页还是异步？" |
| 错误处理 | "网络超时重试几次？报什么错？" |
| 并发/竞态 | "两人同时修改同一记录怎么处理？" |
| 兼容性 | "旧 API 调用者需要兼容吗？" |
| 数据迁移 | "已有数据需要迁移吗？" |

- ✅ 问题必须来自上表中的某个维度
- ❌ 不问技术实现细节
- ❌ 不问读代码就能知道的事

**停下来等待人类回答。这是整个流程中唯一的人工门槛。**

---

### Phase B: 规格化（自动，确认后立即执行）

#### Step 4: 生成 delta spec

根据确认的 proposal + 用户回答，为每个受影响的能力域创建 `changes/<name>/specs/<capability>/spec.md`：

| 情况 | delta spec 区段 |
|------|----------------|
| 全新能力域 | `## ADDED Requirements` — 全部为新增 |
| 修改已有能力域 | `## MODIFIED Requirements` — 完整复制要改的 Requirement 再修改 |
| 删除需求 | `## REMOVED Requirements` — 必须有 Reason 和 Migration |

**每个 Requirement 至少 1 个 Scenario**，使用 WHEN/THEN 格式。

#### Step 5: 生成 tasks.md

参考 `.ai/L3-specs/changes/_change-template/tasks.md`，根据 proposal + delta spec 生成执行步骤：

- **第一组固定为 Tests** — 从 Scenario 的 WHEN/THEN 直接映射为测试用例
- 后续组为实现步骤，按依赖排序
- checkbox 格式：`- [ ] X.Y 描述`
- 每个任务要小到一轮对话能完成

---

### Phase C: TDD 执行（自动）

#### Step 6: 从 Scenario 写测试代码

读取 `.ai/L2-rules/testing.md`（如存在）— 遵守项目测试规范。

对 delta spec 中每个 Scenario，写测试：

- **WHEN** → 测试的 setup + action
- **THEN** → 测试的 assertion
- 覆盖：happy path + edge case + error path

**运行测试，确认全部失败（红灯）。** 如果有测试已通过，说明该行为已存在，检查是否需要调整 spec。

勾选 tasks.md 中 Tests 组的对应 checkbox。

#### Step 7: 实现代码

让测试通过：

1. **强制注入 L2 规则（写任何新代码前）**：完整读取 `.ai/L2-rules/global.md`、`.ai/L2-rules/testing.md`、以及此变更涉及的每个模块的 `L2-rules/<module>.md`。在输出中明列本次要遵守的关键规则（3-5 条）。不允许跳过
2. 跨模块修改 → 先查 `.ai/L1-codebase-map/module-map.md` 变更联动表
3. 创建新文件 → 查 `.ai/L2-rules/templates.md`
4. 实现代码，每一步對比 Step 1 列出的规则
5. **运行测试，确认全部通过（绿灯）**
6. **L2 合规自检（实现完成后，提交前）**：对 Step 7.1 列出的每条关键规则，逐条标注本次代码是否符合：

   ```
   | # | 规则 | 符合？ | 证据 |
   |:--|:-----|:-------|:-----|
   | 1 | [规则描述] | ✅ / 🔴 | [具体代码位置或说明] |
   ```

   有任何 🔴 → 先修复再继续

勾选 tasks.md 中对应实现步骤的 checkbox。

#### Step 8: 收尾

1. 更新 `.ai/L5-validation/traceability/<domain>.md` — 新增的 Scenario 标为 ✅ verified
2. proposal.md 状态改为 `pending-review`
3. tasks.md 所有 checkbox 勾选完毕
4. 更新 `.ai/L4-session/active-session.md` — 记录完成内容和测试结果

---

### 输出格式

Phase A（等待确认时）展示：

```
## 变更提案

**变更名称**: <name>
**受影响能力域**: [列表]

### Why
[1-2 句话]

### What Changes
[具体变更列表]

### 需要确认的业务问题
1. [问题]
2. [问题]
3. [问题]

请确认 proposal 并回答以上问题，确认后我将自动执行：
delta spec → 写测试 → 实现代码 → 测试通过 → 完成
```

Phase C 完成后展示：

```
## 变更完成

**变更名称**: <name>
**状态**: pending-review

### 执行摘要
- Delta spec: [N 个域，ADDED/MODIFIED/REMOVED 数量]
- 测试: [新增 N 个测试用例，全部通过]
- 代码变更: [修改了哪些文件]

### 受影响的 Requirement
| Requirement | Scenario | 测试文件 | 状态 |
|-------------|----------|---------|------|

等待归档（合并 delta spec → 主 spec → 移到 archive/）。
```
