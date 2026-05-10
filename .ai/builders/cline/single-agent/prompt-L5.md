# Cline 构建 L5 验证追溯 — Prompt 模板（单 Agent 模式）

> 将以下 prompt 复制到 Cline 对话中使用。
> 使用前替换 `[项目目录]` 为实际值。
>
> **前置条件**: 已用 `prompt-L1a.md`/`prompt-L1b.md`、`prompt-L2.md`、`prompt-L3.md` 完成 L1/L2/L3 文档生成。
> **本文件范围**: 构建 spec 验证追溯矩阵，验证 L3 spec 与代码实现的一致性。
> **核心差异**: 逐个能力域验证，每个暂停等待人工审核后再继续。

---

## Prompt：构建 L5 验证追溯

````markdown
# 为项目构建 Spec 验证追溯

## 背景

我的项目已有 L1（代码导航）、L2（编码规则）、L3（需求规格），需要构建 L5 验证层，检查 spec 与代码的一致性。

## 目标

[填写范围，如"全量验证"、"只验证 user-auth 域"、"验证最近变更涉及的域"]

## 你的工作步骤

### Step 1: 读取全局上下文

读取以下文件建立基础认知：

- `.ai/L1-codebase-map/overview.md` — 项目功能索引
- `.ai/L3-specs/specs/system.md` — 系统级需求
- `.ai/L5-validation/validation-rules.md` — 验证规则
- `.ai/L5-validation/traceability/_domain-template.md` — 追溯模板
- `.ai/L5-validation/test-specs/_domain-template.md` — 测试用例模板

列出所有能力域和已有文件：

- `ls .ai/L3-specs/specs/`
- `ls .ai/L5-validation/traceability/`
- `ls .ai/L5-validation/test-specs/`

检查项目是否已有测试：

- 搜索 `*.test.*`、`*.spec.*`、`test_*` 等测试文件
- 有测试文件 → **情况 2**（只补缺口）；无测试文件 → **情况 1**（全量生成）

### Step 2: 结构验证

逐个读取 spec 文件，检查格式规范：
- 每个 Requirement 至少有 1 个 Scenario
- Scenario 用 `####` 标题 + WHEN/THEN/AND 格式
- SHALL/MUST/SHOULD/MAY 使用正确
- 无实现细节

**展示结构问题清单，等待人工确认后继续。**

### Step 3: 逐域验证

对每个能力域，逐个执行以下操作：

1. 读取 `specs/<domain>/spec.md`
2. 读取对应的 L1 feature 文档（`features/[功能名]/README.md` + 层文件）
3. 对每条 Requirement 的每个 Scenario：
   - 定位实现代码，验证 WHEN/THEN 是否已实现
   - 搜索测试文件，检查是否有覆盖
   - 标注状态
4. 反向追溯：核心代码路径是否有 spec 覆盖
5. 生成 `traceability/<domain>.md`

**⏸️ 每完成一个域，暂停展示追溯矩阵，等待人工确认后再继续下一个域。**

### Step 4: 生成测试用例设计

对每个域的 traceability 表中 ⚠️/❌ 的 Scenario，生成 `test-specs/<domain>.md`：

- **情况 1（无测试）**：为每个 Scenario 展开完整用例（happy path + edge case + error path）
- **情况 2（有测试）**：只为缺口 Scenario 写用例

每个用例要有具体测试数据，注明 Setup/Teardown。

**⏸️ 每完成一个域的 test-specs，暂停展示用例设计，等待人工确认后继续。**

### Step 5: 生成验证报告

所有域验证完成后，生成 `reports/<YYYY-MM-DD>-<scope>.md`：

- 概要统计（verified / gap / missing 比例）
- 按域明细
- 问题清单（按优先级）
- 建议操作

**展示报告，等待人工确认后写入文件。**
````
