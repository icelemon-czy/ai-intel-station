# Cline 构建 L5 验证追溯 — Prompt 模板

> 将以下 prompt 复制到 Cline 对话中使用。
> 使用前替换 `[项目目录]` 为实际值。
>
> **前置条件**: 已用 `prompt-L1a.md`/`prompt-L1b.md`、`prompt-L2.md`、`prompt-L3.md` 完成 L1/L2/L3 文档生成。
> **本文件范围**: 构建 spec 验证追溯矩阵，验证 L3 spec 与代码实现的一致性。

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

```bash
# 项目总览和功能列表
cat [项目目录]/.ai/L1-codebase-map/overview.md
ls [项目目录]/.ai/L1-codebase-map/features/

# 当前 spec 状态
cat [项目目录]/.ai/L3-specs/specs/system.md
ls [项目目录]/.ai/L3-specs/specs/

# 验证规则和模板
cat [项目目录]/.ai/L5-validation/validation-rules.md
cat [项目目录]/.ai/L5-validation/traceability/_domain-template.md
cat [项目目录]/.ai/L5-validation/test-specs/_domain-template.md
ls [项目目录]/.ai/L5-validation/traceability/
ls [项目目录]/.ai/L5-validation/test-specs/

# 检查项目是否已有测试
find [项目目录] -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*' -o -name '*_test.*' | head -20
```

> **判断场景**：有测试文件 → 情况 2（只补缺口）；无测试文件 → 情况 1（全量生成）。

### Step 2: 结构验证

逐个读取 spec 文件，按 validation-rules.md 的结构验证规则检查格式。
输出结构问题清单。

### Step 3: 正向追溯（使用子任务）

对每个能力域启动子任务：

**子任务指令**（传给 subagent）：

```
验证能力域 [域名]：
1. 读取 specs/[域名]/spec.md
2. 读取 features/[功能名]/README.md 及层文件
3. 对每条 Requirement 的每个 Scenario，在代码中定位实现和测试
4. 输出追溯表（Requirement | Scenario | 实现文件 | 测试文件 | 状态）
5. 执行反向追溯：核心代码路径是否有 spec 覆盖
6. 输出反向追溯表（代码文件 | 行为描述 | 建议）
```

主 agent 收集子任务结果，写入 `traceability/<domain>.md`。

### Step 4: 生成测试用例设计

根据 traceability 表中的缺口，对每个域生成 `test-specs/<domain>.md`：

- **情况 1（无测试）**：为每个 Scenario 展开完整用例（happy path + edge case + error path）
- **情况 2（有测试）**：只为 ⚠️/❌ 的 Scenario 写用例

每个用例要有具体测试数据，注明 Setup/Teardown。

### Step 5: 跨域一致性（全量验证时）

- system.md Cross-Cutting Requirements 是否被各域遵守
- 同一概念跨域是否矛盾
- 域间依赖是否有 spec 体现

### Step 6: 生成验证报告

汇总所有追溯结果，创建 `reports/<YYYY-MM-DD>-<scope>.md`：

- 概要统计
- 按域明细
- 问题清单（按优先级）
- 建议操作

### Step 7: 展示并等待确认

展示追溯矩阵摘要、测试用例设计摘要和问题清单，等待人类确认后写入文件。
````
