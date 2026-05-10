---
name: review-tests
description: "Review test quality by running tests, cross-referencing specs, and hunting false-pass anti-patterns. Designed for loop usage: each invocation reviews ONE target (change or spec domain). Use when: review tests, 审查测试, test coverage, 测试覆盖, 测试够吗, are tests sufficient, 缺什么测试, missing tests, 测试质量, 虚假通过, false pass, 定时审查, scheduled review"
argument-hint: "Optional: specific domain or change name (e.g., 'auth', 'add-csv-export'). If omitted, picks the next target automatically (L3 changes first, then specs)."
---

# Review Tests — 跑测试 + 逐个验证 + 虚假通过狩猎

> 这是工作流中的 **人工门槛 2（Review 批准）** 所在环节。Reviewer 在此决定能不能归档。
>
> **循环使用设计**：本 Skill 每次调用**只审查一个目标**（一个变更 或 一个能力域 spec）。在定时任务 / 外层循环中重复调用，直到队列清空。

## 核心原则

**绝不信任"绿灯"本身。** 只信任 "每个绿灯背后有一个与 spec THEN 精确对齐的 assertion，且该 assertion 实际调用了被测代码"。

本 Skill 的输出是一份**逐测试函数**的审查表。任何测试函数如果无法填满表中所有列，就是缺陷。

## Prerequisites

- `.ai/` 目录已存在且有 L3 + L5 结构
- 项目有测试代码

## Procedure

### Step 0: 选择本次审查目标（单次只选一个）

**0a: 读取测试配置（必做，不可跳过）**

读取 `.ai/L2-rules/testing.md` — 获取以下信息并记录到工作区：
- **测试运行命令**（如 `npm test`、`pytest`、`go test ./...`）
- **测试目录**（如 `__tests__/`、`tests/`、`*_test.go`）
- **测试框架**（如 Jest、pytest、Go testing）

> 如果 `.ai/L2-rules/testing.md` 不存在，告知用户"测试规范缺失，建议先运行 `/setup-testing`"并停止。

**0b: 构建候选队列（按优先级排序）**

按以下**优先级顺序**枚举候选，先到者先审：

```bash
# 优先级 1：L3 变更中 pending-review 状态的变更（按 proposal.md 的创建时间升序）
ls .ai/L3-specs/changes/ | grep -v _change-template
# 对每个变更，读取 proposal.md 中的 status 字段，保留 status == pending-review 的

# 优先级 2：L3 已有 spec（archived 能力域），按能力域字母顺序
ls .ai/L3-specs/specs/ | grep -v _capability-template | grep -v system.md
```

**队列规则**：
1. **P1 优先**：所有 `pending-review` 状态的变更，按创建时间（proposal.md 的 `created` 字段或文件 mtime）升序
2. **P2 兜底**：当 P1 为空时，按能力域字母顺序遍历 `.ai/L3-specs/specs/` 中的所有 spec

**0c: 选择本次目标（单个）**

| 用户参数 | 动作 |
|:---------|:-----|
| 指定了变更名/域名 | 目标 = 该指定项 |
| 未指定 | 目标 = 候选队列中的**第一项**（P1 优先，P1 空则 P2 首项） |

**0d: 去重（避免循环重复审查）**

读取 `.ai/L5-validation/reports/` 下最近的 review 报告（如存在）。如果 P2 队列（spec 类目标）最近一次审查时间 < 配置的冷却期（默认 7 天）且无代码变更 → 跳到下一项。

> 冷却规则：可在 `.ai/L2-rules/global.md` 的 `review-tests.cooldown-days` 字段配置。

**输出本次目标**（必填，后续所有 Step 围绕该单一目标展开）：

```
## 本次审查目标
- 类型: [change | spec-domain]
- 名称: [e.g., add-csv-export / auth]
- 优先级来源: [P1 pending-review / P2 routine sweep]
- 队列剩余: [N 项未审，下次调用将审查 <下一项名称>]
```

如果候选队列为空 → 输出 `队列空，无需审查`，结束。

**0e: 收集本次目标的 Scenario 清单**

只读取 0c 选定的**单个目标**的 spec：
- 目标是 change → `.ai/L3-specs/changes/<change-name>/specs/*/spec.md`（delta spec）
- 目标是 spec-domain → `.ai/L3-specs/specs/<domain>/spec.md`

枚举该目标下的每一个 Requirement 和 Scenario。填入下表（后续步骤逐列填充）：

```
| # | Requirement | Scenario | Spec THEN（逐字摘抄） | 测试函数 | 测试文件:行 | 实际 assertion | 调用链验证 | 反模式命中 | 反向推理 | 结论 |
```

**此表是本 Skill 的核心输出。每一行必须填满所有列，空列 = 缺陷。**

### Step 1: 逐 Scenario 定位测试（穷举，非抽样）

对 Step 0 表中的**每一行**：

#### 1a: 从 Spec Scenario 逐字摘抄 THEN

打开对应 `spec.md`，找到该 Scenario 的 THEN 子句，**逐字复制**到表的"Spec THEN"列。不要改写、概括或省略。

#### 1b: 定位对应测试函数

用以下策略定位（按优先级尝试）：

1. `traceability/<domain>.md` 中该 Scenario 对应的测试文件:行号 → 直接打开
2. grep 测试目录中与 Scenario 关键词匹配的 test 函数名/describe 块：
   ```bash
   grep -rn "scenario关键词\|requirement关键词" <test-dir>
   ```
3. 如果 1、2 均找不到 → 该 Scenario **无测试**，"测试函数"列填 `❌ 缺失`，直接标为 🔴 打回项

#### 1c: 逐字比对 assertion vs Spec THEN

打开测试函数后，**逐个 assertion** 做如下比对：

| 检查项 | 方法 | 通过条件 |
|:-------|:-----|:---------|
| assertion 存在 | 在测试函数体内 grep `assert\|expect\|should\|verify\|check` | ≥ 1 个 assertion |
| assertion 对齐 THEN | 逐字读 assertion 的实际比较值，与"Spec THEN"列逐条对比 | 每个 THEN 子句都有对应 assertion |
| assertion 强度 | 看 assertion 的比较方式 | 不得仅 `toBeTruthy/toBeNotNull/>=0`；必须比对**具体预期值** |

把每个 assertion 的**实际内容**写入表的"实际 assertion"列。例：
- ✅ `expect(response.status).toBe(401)` — 对齐 THEN "返回 401"
- ❌ `expect(response).toBeTruthy()` — 只验证有返回，不验证状态码

### Step 2: 调用链验证（关键，防止 Mock 架空）

对 Step 1 中有测试的每一行：

#### 2a: 从测试函数反向追踪

读测试函数的 setup（`beforeEach`、`beforeAll`、函数调用），找到**被测的入口函数/方法**。

#### 2b: 确认被测函数是真实代码而非 Mock

具体检查：

```
1. 测试 import 的模块 → 是不是从源代码目录导入的？（而不是 __mocks__/）
2. 有没有 jest.mock()、sinon.stub()、patch() 作用在被测函数本身？
   - mock 外部依赖（DB、HTTP）= ✅ 正常
   - mock 被测函数本身 = 🔴 致命（反模式 #4）
3. setup 中的 fixture/test data → 是否能触发 Spec WHEN 条件？
   - 例：Spec 说 "WHEN 密码为空"，但 test data 用了 password="test123" → 🔴 没测到
```

填入表的"调用链验证"列：
- `✅ 真实调用 <函数名>`
- `⚠️ mock 了 <X>，可接受（外部依赖）`
- `🔴 mock 了被测函数本身` 或 `🔴 test data 不触发 WHEN`

### Step 3: 虚假通过狩猎（逐测试函数，强制全量）

对 Step 1-2 幸存（非 ❌）的每个测试函数，用以下 **7 + N 条反模式清单逐条过**。

**不允许跳过任何一条。每条必须在输出中明确标注 ✅ 通过 / 🔴 命中。**

| # | 反模式 | 检测算法（AI 必须按此操作） | 风险 |
|:--|:-------|:--------------------------|:-----|
| 1 | **断言缺失** | 在测试函数体内 grep `assert\|expect\|should\|verify`。数量 = 0 → 命中 | 🔴 |
| 2 | **断言太弱** | 列出所有 assertion。如果任何一个只做 `toBeTruthy()\|toBeDefined()\|toBeNotNull()\|!= null\|!= undefined\|>= 0` 而不比对具体预期值 → 命中 | 🔴 |
| 3 | **Happy path only** | 统计该 Requirement 下所有 Scenario。如果只有 1 个正常路径 test，缺 edge case / error path → 命中。**具体**：对照 spec，看是否有 "WHEN 异常/边界输入 THEN ..." 的 Scenario 没被覆盖 | 🔴 |
| 4 | **Mock 了要测的东西** | Step 3b 已检查。"调用链验证"列为 🔴 → 命中 | 🔴 |
| 5 | **Assertion 绕开 Spec THEN** | Step 2c 已检查。比对"Spec THEN"列和"实际 assertion"列。如果 assertion 验证的内容和 THEN 说的不是同一件事 → 命中。**例**：THEN 说"返回 400 + 错误码 INVALID_EMAIL"，assertion 只检查 `status !== 500` | 🟡 |
| 6 | **条件永真** | 检查是否存在：`expect(x).toBe(x)` / `expect(true).toBe(true)` / assert 在 `if(true)` 块里 / 空 snapshot 文件 / snapshot 内容为 `{}` 或 `""` | 🔴 |
| 7 | **吞异常** | 检查测试中的 try-catch：`catch` 块是否为空 / 只有 `console.log` / 没有 `expect`。应该 `expect(error.message).toContain(...)` | 🔴 |

> **项目自定义反模式**（第 8+ 条）：读取 `.ai/L2-rules/testing.md` 的"自定义反模式"区段，逐条追加检查。前 7 条是底线，不可删除。

**输出格式（每个测试函数必须输出）**：

```
#### [测试文件:行] — [测试函数名]
对应 Scenario: [Requirement / Scenario 名]

| # | 反模式 | 结果 | 证据 |
|:--|:-------|:-----|:-----|
| 1 | 断言缺失 | ✅ 通过 | 2 个 expect |
| 2 | 断言太弱 | 🔴 命中 | `expect(result).toBeTruthy()` 应改为 `expect(result.code).toBe('INVALID')` |
| 3 | Happy path only | ✅ 通过 | 同 Requirement 下另有 error-path test |
| 4 | Mock 被测函数 | ✅ 通过 | mock 的是 DB client，不是被测函数 |
| 5 | 绕开 THEN | ✅ 通过 | assertion 检查 status=401，与 THEN 一致 |
| 6 | 条件永真 | ✅ 通过 | 无自证循环 |
| 7 | 吞异常 | ✅ 通过 | 无 try-catch |
```

### Step 4: 跑对应测试 + 检查异常标记

基于 Step 1 中定位到的测试文件，运行**对应的测试**（非全量）：

```bash
# 只运行审查范围内的相关测试文件（按框架调整）：
# Jest:   npx jest <相关测试文件1> <相关测试文件2>
# pytest: pytest <相关测试文件1> <相关测试文件2>
# Go:     go test ./pkg/... -run "TestA|TestB"
<0a 中读到的测试运行命令> <Step 1b 中定位到的测试文件>

# 扫描测试异常标记（只在相关文件中）
grep -rn "\.skip\|\.only\|xit(\|xdescribe(\|xtest(\|@Disabled\|@Ignore\|pytest\.mark\.skip\|@unittest\.skip\|pending(" <Step 1b 定位到的测试文件>
```

根据结果分支：

| 测试结果 | 处理 |
|:---------|:-----|
| ❌ 有测试失败 | **如果本次目标是 change，先将 proposal.md 状态改为 `review-failed`，追加 Review Feedback，再转 `/fix-bug`；如果本次目标是 spec-domain，则直接带失败输出转 `/fix-bug`**。本 Skill 到此结束 |
| ⚠️ 有 skip/only/pending 标记 | **记录到报告的"异常标记"区段**，每个 skip 必须有 reason，否则标为问题。`.only` 一律标为 🔴 高风险（说明其他测试被静默跳过） |
| ✅ 全绿且无异常标记 | 继续 Step 5 |

### Step 5: 反向推理 — "删掉代码还能绿吗？"

对每个**关键 assertion**（Step 1c 识别的），做以下思维实验：

> 如果我把被测函数中实现这个行为的那几行代码**注释掉**（或改成 `return null`），这个测试会变红吗？

| 推理结果 | 含义 |
|:---------|:-----|
| 会变红 | ✅ 测试有效 |
| 不会变红 | 🔴 测试无效——assertion 没有实际检验被测行为（可能测的是 mock 返回值、默认值、或另一个函数的输出） |
| 不确定 | ⚠️ 标记为需人工复核 |

**不需要真的删代码跑测试。** 这是一个**阅读级推理**——看被测函数的实现，判断 assertion 检查的值是否来自那段实现代码。

把结论填入主表的"反向推理"列。

### Step 6: 覆盖缺口分析

在 Scenario 层面已经逐行检查完，现在做**补充**覆盖检查：

#### 6a: 没有 Scenario 的代码路径

```bash
# 列出变更涉及的源码文件
git diff --name-only HEAD~N -- <src-dir>
```

对每个变更的源码文件，快速扫描分支（`if/else`、`switch`、`try/catch`、guard clause）。对照 Spec Scenarios，是否有代码分支没有任何 Scenario 覆盖？

如果有 → 登记为"缺失 Scenario"，建议补 spec + 补测试。

#### 6b: 边界值检查

对每个 Scenario 的 WHEN 输入参数：

| 输入 | 需要的边界值 | 已有？ |
|:-----|:------------|:-------|
| 字符串 | 空串 `""`、超长、特殊字符 | ? |
| 数字 | 0、负数、最大值、小数 | ? |
| 集合 | 空集、1 个、满/超限 | ? |
| 可选 | null / undefined / 缺失 | ? |

已有 = 对应 Scenario 的 test data 包含此边界。未有 → 登记为"缺失边界"。

### Step 7: 输出审查报告

```
## 测试审查报告

### 执行结果
- 测试运行: ✅ 全绿 / ❌ N 个失败（已转 /fix-bug）
- 异常标记: [.skip/.only/pending 列表，或"无"]
- 审查范围: [变更名 / 能力域]

### 主表（每行 = 一个 Spec Scenario）

| # | Req | Scenario | Spec THEN | 测试函数 | 实际 assertion | 调用链 | 反模式 | 反向推理 | 结论 |
|:--|:----|:---------|:----------|:---------|:---------------|:-------|:-------|:---------|:-----|
| 1 | REQ-001 | 正常登录 | 返回200+token | login.test:45 | status=200, body.token存在 | ✅ 真实调用 handleLogin | ✅ 全通过 | ✅ 删handleLogin会红 | ✅ |
| 2 | REQ-001 | 空密码 | 返回400+PASSWORD_REQUIRED | — | — | — | — | — | 🔴 无测试 |
| 3 | REQ-002 | Token过期 | 自动刷新 | refresh.test:12 | expect(newToken).toBeDefined() | ✅ 调用 refresh() | 🔴 #2 断言太弱 | ⚠️ 可能测的是默认值 | 🔴 |

### 覆盖概要

| 能力域 | Requirement | Scenario | ✅ 有效 | 🔴 缺陷 | ❌ 缺失 |
|:-------|:-----------|:---------|:--------|:--------|:--------|
| auth | 3 | 7 | 4 (57%) | 2 (29%) | 1 (14%) |

### 反模式统计

| 反模式 | 命中次数 | 涉及测试 |
|:-------|:---------|:---------|
| #2 断言太弱 | 2 | refresh.test:12, logout.test:8 |
| #5 绕开 THEN | 1 | login.test:92 |

### 覆盖缺口

| 类型 | 描述 | 建议 |
|:-----|:-----|:-----|
| 缺失 Scenario | handleLogin 有 rate-limit 分支，无对应 Scenario | 补 spec + 补测试 |
| 缺失边界 | REQ-001 空密码 无测试 | 补测试 |

### 结论（必填，三选一）

- [ ] ✅ 通过 — 主表所有行结论为 ✅，无 🔴 反模式，无 ❌ 缺失 → 可以 `/archive-change`
- [ ] ⚠️ 有缺口但非阻塞 — 有 ⚠️ 但无 🔴 → 登记到 Known Gaps，允许归档
- [ ] ❌ 打回 — 有任何 🔴 或 ❌ → 必须 `/fix-bug` 再回来

### 打回原因（如适用）
1. 🔴 [file:line] 反模式 #N：[描述] → /fix-bug Step 3B
2. ❌ [Req/Scenario] 无测试 → /fix-bug Step 3B 补测试
```

**结论判定规则（不允许 AI 自由裁量）**：

| 主表中存在 | 结论 |
|:-----------|:-----|
| 任何 🔴（反模式命中 / 反向推理失败）| ❌ 打回 |
| 任何 ❌（Scenario 无测试） | ❌ 打回 |
| 只有 ⚠️（标记为需人工复核） | ⚠️ 有缺口但非阻塞 |
| 全部 ✅ | ✅ 通过 |

### Step 8: 状态回流

> 以下状态回流仅适用于 **change** 目标。若本次审查目标是 `spec-domain`，则不改 proposal.md 状态，只更新报告和 `.ai/L4-session/active-session.md`。

根据 Step 7 结论：

| 结论 | 变更状态流转 |
|:-----|:-------------|
| ✅ 通过 | `pending-review` → `approved`，提示用户运行 `/archive-change` |
| ❌ 打回 | `pending-review` → `review-failed`（记录在 proposal.md 的 Review Feedback），提示用户运行 `/fix-bug`；由 `/fix-bug` 再推进到 `implementing` |
| ⚠️ 有缺口但非阻塞 | `pending-review` → `approved`，问题登记到 proposal.md 的"Known Gaps" |

更新 `.ai/L4-session/active-session.md`，记录审查结果和下一步动作。

**生成审查报告文件**：将完整报告写入 `.ai/L5-validation/reports/review-<target-name>-<YYYYMMDD>.md`，供冷却期判断（Step 0d）复用。

### Step 9: 循环出口提示（单次结束）

本次调用到此结束。**不要自动继续审查下一项**。输出如下循环提示供外层调度器使用：

```
## 循环状态
- 本次已审查: [目标类型/名称]
- 本次结论: [✅ 通过 / ⚠️ 非阻塞 / ❌ 打回]
- 队列剩余: [N 项]
- 下次调用将审查: [下一项名称，或"队列空"]
```

> **定时任务接入**：外层 scheduler 每次调用本 Skill，读取"下次调用将审查"字段作为下次 argument；当输出"队列空"时停止循环。

## 反模式（Reviewer 禁止）

- ❌ 单次调用审查多个目标（违反循环设计；每次只审一个）
- ❌ 不跑对应测试就签字通过
- ❌ 只看 traceability 的 ✅，不打开测试文件读 assertion
- ❌ 发现虚假通过只记录不打回（主表有 🔴 → 必须打回）
- ❌ 跳过虚假通过清单的某几条（7 条是底线，逐条标注结果；项目可追加，但不可删除）
- ❌ 主表输出时省略列（"调用链验证"和"反向推理"两列最容易被跳过——不允许）
- ❌ 对某个 Scenario 写"已覆盖"但不填写"实际 assertion"列的具体内容
- ❌ 抽样检查（本 Skill 要求穷举当次目标内的每个 Scenario）

