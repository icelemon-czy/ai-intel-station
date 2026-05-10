# Copilot 构建 L5 验证追溯 — Prompt 模板

> 将以下 prompt 复制到 Copilot Chat 对话中使用。
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

# 已有追溯和测试用例（如有）
ls [项目目录]/.ai/L5-validation/traceability/
ls [项目目录]/.ai/L5-validation/test-specs/

# 检查项目是否已有测试
find [项目目录] -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*' -o -name '*_test.*' | head -20
```

> **判断场景**：如果 find 返回测试文件 → 项目已有测试（情况 2）；否则 → 项目无测试（情况 1）。

### Step 2: 结构验证

对 system.md 和每个能力域 spec 执行格式检查：

```bash
# 逐个读取 spec
cat [项目目录]/.ai/L3-specs/specs/system.md
cat [项目目录]/.ai/L3-specs/specs/[域名]/spec.md
```

检查项（来自 validation-rules.md）：
- 每个 Requirement 至少有 1 个 Scenario
- Scenario 用 `####` 标题 + WHEN/THEN/AND 格式
- SHALL/MUST/SHOULD/MAY 使用正确
- 无实现细节

**输出**：结构问题清单。如有问题，先修复再继续。

### Step 3: 逐域正向追溯

对每个能力域：

1. **读取 spec**：
   ```bash
   cat [项目目录]/.ai/L3-specs/specs/[域名]/spec.md
   ```

2. **读取对应的 L1 feature 文档**：
   ```bash
   cat [项目目录]/.ai/L1-codebase-map/features/[功能名]/README.md
   # 按需深入各层文件
   ```

3. **对每条 SHALL/MUST Requirement 的每个 Scenario**：
   - 根据 L1 feature 文档定位实现代码
   - 读取代码验证 WHEN 条件是否被处理、THEN 结果是否被产出
   - 搜索测试文件中是否有覆盖该 Scenario 的用例
   - 标注状态：verified / untested / partial / unimplemented

4. **对 SHOULD 级别**：同样追溯，但允许 unimplemented

5. **对 MAY 级别**：记录但不标记为问题

### Step 4: 反向追溯

对每个域的核心代码路径：

1. 从 L1 feature 文档找到核心业务逻辑文件
2. 快速扫描 public API、业务规则、数据变换、边界校验
3. 检查是否有对应 spec 覆盖
4. 标记 no-spec 的代码路径

> 聚焦核心逻辑，忽略工具函数和框架代码。

### Step 5: 生成追溯矩阵

对每个验证过的域，创建或更新 `L5-validation/traceability/<domain>.md`：

```bash
# 参考模板
cat [项目目录]/.ai/L5-validation/traceability/_domain-template.md
```

填写追溯表和反向追溯部分。

### Step 6: 生成测试用例设计

根据 traceability 表中的缺口，生成 `test-specs/<domain>.md`：

```bash
# 参考模板
cat [项目目录]/.ai/L5-validation/test-specs/_domain-template.md
```

**项目无测试（情况 1）**：
- 为每个 Scenario 展开完整用例（happy path + edge case + error path）
- SHALL/MUST 级别的 Scenario 必须有边界用例

**项目有测试（情况 2）**：
- 只为 traceability 表中 ⚠️ untested / ⚠️ partial / ❌ unimplemented 的 Scenario 写用例
- 已经 ✅ verified 的跳过

每个用例要有**具体测试数据**（不能只写"valid input"），注明 Setup/Teardown。

### Step 7: 跨域一致性（全量验证时）

如果是全量验证：
- 检查 system.md 的 Cross-Cutting Requirements 是否被各域遵守
- 检查同一概念在不同域中是否有矛盾描述
- 检查域间依赖是否在 spec 中有体现

### Step 8: 生成验证报告

创建 `L5-validation/reports/<YYYY-MM-DD>-<scope>.md`，包含：

```markdown
# 验证报告 — <date> (<scope>)

## 概要
- 能力域: N | Requirement: N | Scenario: N
- ✅ verified: N (%) | ⚠️ gap: N (%) | ❌ missing: N (%)

## 按域明细
[每个域的追溯汇总]

## 问题清单（按优先级）
1. **高** — SHALL/MUST 未实现
2. **中** — 无测试覆盖
3. **低** — 代码无 spec 覆盖

## 建议
- [ ] [具体操作建议]
```

### Step 9: 展示并等待确认

展示：
1. 结构验证结果
2. 各域追溯矩阵摘要
3. 测试用例设计摘要（每域多少用例，覆盖多少 Scenario）
4. 问题清单和建议

等待人类确认后写入文件。
````
