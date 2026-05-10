---
name: archive-change
description: "Archive a completed change: merge delta spec into main specs, move to archive, update traceability. Use when: 归档, archive, 合并spec, merge spec, 变更完成, change done, 审核通过, approved"
argument-hint: "Optional: change name (e.g., 'add-csv-export'). Omit to list approved changes."
---

# Archive Change

变更完成后，将 delta spec 合并到主 spec，移动到 archive，更新追溯。

> **前置条件**：变更的 proposal.md 状态为 `approved`，且所有测试通过。

## Procedure

---

### Step 1: 定位变更

**有参数** → 直接读取 `.ai/L3-specs/changes/<name>/proposal.md`，确认状态为 `approved`。

**无参数** → 扫描所有 `approved` 状态的变更：

```bash
ls .ai/L3-specs/changes/ | grep -v _change-template
```

对每个变更读取 proposal.md 的状态，只展示 `approved` 的：

```
## 待归档变更

| # | 变更名 | 目的 |
|---|--------|------|
| 1 | add-csv-export | 报表支持 CSV 导出 |

请选择一个编号进行归档：
```

如无 `approved` 的变更，告知用户"没有待归档的变更"并停止。

**等用户选择后继续。**

---

### Step 2: 展示变更摘要 → 等人确认

读取变更的完整内容（**逐个文件读取，不可跳过**）：
1. 读取 `.ai/L3-specs/changes/<name>/proposal.md` — 确认状态和变更目的
2. 读取 `.ai/L3-specs/changes/<name>/specs/` 下所有 delta spec — 了解新增/修改/删除了哪些 Requirement
3. 读取 `.ai/L3-specs/changes/<name>/tasks.md`（如存在）— 确认任务完成状态

展示归档预览：

```
## 归档预览: <change-name>

### Delta Spec 合并计划
| 能力域 | 操作 | Requirement 数量 |
|--------|------|-----------------|
| auth | MODIFIED | 2 |
| export | ADDED (新能力域) | 3 |

### 测试状态
- tasks.md: X/X 完成
- 所有测试通过: ✅

确认归档？（合并 delta spec 到主 spec + 移动到 archive）
```

**停下来等待人类确认。**

---

### Step 3: 合并 delta spec 到主 spec

对变更的 `specs/` 下每个能力域：

1. 读取 delta spec（`changes/<name>/specs/<cap>/spec.md`）
2. 读取主 spec（`.ai/L3-specs/specs/<cap>/spec.md`，如存在）

按区段执行：

| Delta 区段 | 操作 |
|-----------|------|
| `## ADDED Requirements` | 追加到主 spec 的 Requirements 末尾 |
| `## MODIFIED Requirements` | 找到同名 Requirement，**整块替换**（不做 patch 级合并）|
| `## REMOVED Requirements` | 删除同名 Requirement 块 |
| 新能力域（主 spec 不存在） | 从 `_capability-template/` 创建新 `specs/<cap>/spec.md`，写入所有 Requirement |

#### 合并示例（MODIFIED）

**主 spec 中原有**：
```markdown
### Requirement: 用户登录
The system SHALL authenticate users by username and password.

#### Scenario: 正常登录
- WHEN 用户提供正确用户名密码
- THEN 返回 200 和 session token
```

**delta spec MODIFIED 块**：
```markdown
## MODIFIED Requirements

### Requirement: 用户登录
The system SHALL authenticate users by username and password,
**and MUST reject empty passwords with 400**.

#### Scenario: 正常登录
- WHEN 用户提供正确用户名密码
- THEN 返回 200 和 session token

#### Scenario: 空密码（新增）
- WHEN 用户提供空密码
- THEN 返回 400，错误码 PASSWORD_REQUIRED
```

**合并后主 spec**：
```markdown
### Requirement: 用户登录
The system SHALL authenticate users by username and password,
**and MUST reject empty passwords with 400**.

#### Scenario: 正常登录
- WHEN 用户提供正确用户名密码
- THEN 返回 200 和 session token

#### Scenario: 空密码
- WHEN 用户提供空密码
- THEN 返回 400，错误码 PASSWORD_REQUIRED
```

> **规则**：MODIFIED 是整个 Requirement 块整块替换，不是句子级 diff。写 delta 时必须复制原 Requirement 再改。

---

### Step 4: 更新追溯

读取 `.ai/L5-validation/traceability/<domain>.md`（对每个涉及的能力域），然后更新：

- ADDED Requirement 的 Scenario → 确认标为 ✅ verified。**确认方法**：检查该变更是否已通过 `/review-tests` 且报告结论为 ✅ 或 ⚠️；如果没有（例如在归档前未运行 review-tests），**必须先运行 `/review-tests`** 再回来归档
- MODIFIED Requirement 的 Scenario → 确认状态仍正确（按同样方法检查 review-tests 报告）
- REMOVED Requirement 的 Scenario → 从追溯文件中移除

---

### Step 5: 移动到 archive

1. proposal.md 状态改为 `archived`
2. 移动整个目录：`changes/<name>/` → `archive/<name>/`
3. 如果 `.ai/L4-session/active-session.md` 指向该变更 → 清除引用

```bash
mkdir -p .ai/L3-specs/archive/
mv .ai/L3-specs/changes/<name>/ .ai/L3-specs/archive/<name>/
```

---

### Step 6: 验证

1. 主 spec 结构完整性检查（逐条验证，任何一条失败 → 报错并停止）：
   - [ ] 每个 Requirement 以 `### Requirement:` 开头
   - [ ] 每个 Requirement 下至少有 1 个 `#### Scenario:`
   - [ ] 每个 Scenario 包含 `WHEN` 和 `THEN`（可以搜索关键词确认）
   - [ ] 无孤立的 Scenario（即 Scenario 前必须有 Requirement 父级标题）
   - [ ] 无重复的 Requirement 名称（`grep -c '### Requirement: <名称>' spec.md` 应 = 1）
2. 追溯文件与主 spec 一致（追溯文件中的 Scenario 数量 = 主 spec 中的 Scenario 数量）
3. `changes/` 下已无该变更

展示合并后受影响的主 spec 变化摘要：

```
## 归档完成: <change-name>

### 主 spec 变化
- specs/auth/spec.md: 修改 2 个 Requirement
- specs/export/spec.md: 新建，3 个 Requirement

### 追溯更新
- traceability/auth.md: 2 个 Scenario 状态确认
- traceability/export.md: 新建，3 个 Scenario ✅

变更已移至 archive/<change-name>/。
```
