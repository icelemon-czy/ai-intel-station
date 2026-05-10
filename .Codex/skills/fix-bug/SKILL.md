---
name: fix-bug
description: "Unified bug-fix entry: triage root cause (code / test / spec) then fix with spec-first discipline. Designed for loop usage: each invocation fixes ONE bug. Use when: bug, 有bug, 行为不对, unexpected behavior, fix issue, 修bug, 不符合预期, something broken, 测试失败, test failed, review 打回, review failed, 虚假通过, false pass, 定时修复, scheduled fix"
argument-hint: "Describe the specific bug to fix (e.g., 'review 打回：登录用例没覆盖空密码', '导出的 CSV 缺少 header'). If omitted, picks the next bug from the queue automatically."
---

# Fix Bug — 统一修复入口（含分诊）

任何"不对劲"都走这个 Skill：测试红灯、review 打回、线上行为异常、虚假通过。
Skill 内部**自动分诊**，分辨是 **代码 Bug / 测试 Bug / Spec 歧义** 中的哪一种，再按对应路径修复。

> **核心纪律**：绝不先改代码。先定位"正确行为"（spec），再确认"怎么验证"（test），最后才动手修（code）。
>
> **循环使用设计**：本 Skill 每次调用**只修一个 bug**。在定时任务 / 外层循环中重复调用，直到 bug 队列清空。

## 覆盖场景

| 触发场景 | 所处变更状态 | 修完后回到 |
|:---------|:------------|:-----------|
| `/review-tests` 红灯 / review 打回 | `review-failed` → `implementing` | `pending-review` |
| 开发中测试突然挂了 | `implementing` | 继续 `implementing` |
| 已归档功能出现 bug（原 `/spec-fix` 用例） | `archived` | 新建 fix 变更 |
| Reviewer 发现"虚假通过"（测试绿但行为错） | `review-failed` → `implementing` | `pending-review` |

## Prerequisites

- `.ai/` 目录已存在且有 L1 + L3 + L5 结构

## Procedure

### Step 0: 选择本次修复目标（单次只修一个）

**0a: 构建 bug 队列（按优先级排序）**

按以下**优先级顺序**枚举候选 bug：

```
P1 — review 打回（阻塞归档，最高优先）
   来源：.ai/L5-validation/reports/ 下最近报告中结论为 ❌ 打回 的条目
   来源：proposal.md 中 status == review-failed 的变更的 "Review Feedback" 列表
P2 — 开发中失败的测试
   来源：当前 implementing 状态变更中 tasks.md 标记为失败 / 未完成验证的项
P3 — 已归档功能的新 bug 报告
   来源：用户显式输入的 bug 描述（无对应 pending 变更）
```

**0b: 选择本次目标（单个 bug）**

| 用户参数 | 动作 |
|:---------|:-----|
| 指定了具体 bug 描述 | 目标 = 该描述（跳过队列扫描） |
| 未指定 | 目标 = 队列中的**第一个** bug（P1 > P2 > P3 优先） |

**输出本次目标**（必填，后续所有 Step 围绕该单一 bug 展开）：

```
## 本次修复目标
- 来源: [P1 review-failed / P2 test-red / P3 archived-bug-report]
- 描述: [具体 bug 描述]
- 关联变更: [change-name 或 "无（需新建 fix 变更）"]
- 队列剩余: [N 个 bug 未修]
```

如果队列为空且用户未指定 → 输出 `队列空，无需修复`，结束。

### Step 1: 场景识别（自动）

根据 Step 0 选中的 bug 和上下文自动判断所处场景：

1. `ls .ai/L3-specs/changes/` — 是否有 `review-failed` 或 `implementing` 状态的变更涉及相关功能？
   - 有 → 这是 "开发中修复" 或 "review 打回"，记下变更名
   - 无 → 这是 "已归档功能 bug"，稍后需要新建 fix 变更
2. 记录"当前变更上下文"供后续步骤使用

### Step 2: 定位相关 spec

1. 读取 `.ai/L1-codebase-map/overview.md` — 匹配涉及的功能
2. 读取对应的 `features/[name]/README.md` — 理解数据流和相关代码
3. 读取 `.ai/L3-specs/specs/` 下对应能力域的 `spec.md` — 找到相关 Requirement + Scenario
4. 若 Step 1 识别到进行中的变更 → 同时读取该变更的 delta spec

### Step 3: 分析 Bug + 定位相关测试 + 分诊（关键步骤）

**3a: 读取测试配置（必做，不可跳过）**

读取 `.ai/L2-rules/testing.md` — 获取：
- **测试运行命令**（如 `npm test`、`pytest`、`go test ./...`）
- **测试目录**
- **测试框架**

读取 `.ai/L2-rules/testing.md` — 获取：
- **测试运行命令**（如 `npm test`、`pytest`、`go test ./...`）
- **测试目录**
- **测试框架**

> 如果 `.ai/L2-rules/testing.md` 不存在，告知用户"测试规范缺失，建议先运行 `/setup-testing`"并停止。

**3b: 先分析 Bug，定位相关代码和测试（必须先于跑测试）**

基于 Step 2 中找到的 spec + Step 0 选中的 bug 描述：

1. 根据 spec 中涉及的 Requirement/Scenario，定位对应的**源码文件**（参考 `features/[name]/README.md` 中的层导航表）
2. 在测试目录中 grep 相关关键词，定位**对应的测试文件和测试函数**：
   ```bash
   grep -rn "scenario关键词\|requirement关键词\|函数名" <3a 中的测试目录>
   ```
3. 阅读相关测试代码，理解现有 assertion 验证的是什么
4. 记录下"相关测试文件列表"供 3c 使用

**3c: 跑对应测试（非全量）**

只运行 3b 中定位到的相关测试（使用框架提供的文件/函数级过滤），拿到失败输出（或确认全绿但行为仍错）。

```bash
# 示例（按框架调整）：
# Jest:   npx jest <相关测试文件>
# pytest: pytest <相关测试文件>::<测试函数>
# Go:     go test ./pkg/... -run <TestName>
```

> 如果 3b 未能定位到任何相关测试 → 该 Scenario **无测试**，直接判定为根因 E（Spec 缺失/测试缺失）→ Step 4C。

**3d: 分诊**

基于 3b 的代码阅读 + 3c 的测试结果，按以下**决策树**逐步分诊（不要凭整体感觉判断，严格按分支走）：

```
Q1: 有测试失败吗？
├── 是 → Q2: 找到对应 Spec 的 WHEN/THEN 了吗？
│   ├── 是 → Q3: 测试 assertion 和 Spec THEN 说的是同一件事吗？
│   │   ├── 是（assertion 正确，代码没实现对）→ 根因 A: 代码 Bug → Step 4A
│   │   └── 否（assertion 写错了/mock 错了）→ 根因 B: 测试 Bug → Step 4B
│   └── 否（Spec 中找不到对应 Requirement）→ 根因 E: Spec 缺失 → Step 4C
└── 否（全绿但行为错）→ Q4: 行为不对的那个场景，Spec 中有 THEN 吗？
    ├── 是 → Q5: 测试 assertion 验证了那个 THEN 吗？
    │   ├── 是但 assertion 太弱（如 toBeTruthy）→ 根因 C: 虚假通过 → Step 4B
    │   └── 否（assertion 验证的是别的东西）→ 根因 C: 虚假通过 → Step 4B
    └── 否 → Q6: Spec 描述模糊还是完全没有？
        ├── 模糊（对同一 WHEN 有两种 THEN 解读）→ 根因 D: Spec 歧义 → Step 4C
        └── 完全没有 → 根因 E: Spec 缺失 → Step 4C
```

分诊结果对照表（决策树终端节点的归总）：

| # | 情况 | 判据 | 根因分类 | 处理路径 |
|:--|:-----|:-----|:---------|:---------|
| A | 测试红 + assertion 与 spec THEN 一致 | 测试正确，代码没实现对 | **代码 Bug** | → Step 4A |
| B | 测试红 + assertion 与 spec THEN 不一致 | 测试写错了（断言写反、mock 错、数据错） | **测试 Bug** | → Step 4B |
| C | 测试绿但行为错 / 覆盖不到 | 测试只过了 happy path，缺 edge case；或 assert 太弱 | **虚假通过** | → Step 4B（补/改测试让它红，再 Step 4A） |
| D | Spec 本身模糊，代码/测试理解不一致 | 对同一 WHEN 有两种 THEN 解读 | **Spec 歧义** | → Step 4C |
| E | Spec 完全没覆盖这个行为 | 功能已存在但 spec 找不到对应 Requirement | **Spec 缺失** | → Step 4C |

**把分诊结论明确告知用户**：

```
## 分诊结论
根因类型: [A/B/C/D/E]
证据: [具体的 spec 条款 / 测试代码片段 / 失败输出]
下一步: [对应的 Step 4X]
```

### Step 4A: 代码 Bug 路径

1. 读取 `.ai/L2-rules/global.md` + 相关模块规则
2. 读取 `.ai/L1-codebase-map/features/<相关功能>/README.md` — 定位 bug 代码位置（层导航表、数据流）
3. 修复代码
4. 跑测试，确认由红转绿
5. 跳到 Step 5

### Step 4B: 测试 Bug / 虚假通过路径

1. 读取 `.ai/L2-rules/testing.md`
2. 对照 spec 的 WHEN/THEN 重写 / 加强测试：
   - 断言写反 → 修正断言
   - Mock 错 → 修正 mock，最好换成更真实的 fixture
   - 虚假通过 → 补 edge case / error path，让测试能真正暴露问题。**识别要补哪些 edge case 的算法**：对照 Spec 中该 Requirement 的所有 WHEN 输入参数，按以下边界值表逐项检查：
     - 字符串：空串 `""`、超长、特殊字符（`<script>`、`' OR 1=1`）
     - 数字：0、负数、最大值、小数
     - 集合：空集、1 个、满/超限
     - 可选参数：null / undefined / 缺失
     
     已有 Scenario 覆盖的 → 跳过。未覆盖的 → 补测试
3. 跑测试，**确认此时测试是红的**（证明它有辨别能力）
4. 如果是虚假通过导致代码也有问题 → 继续 Step 4A 修代码
5. 跳到 Step 5

### Step 4C: Spec 歧义 / 缺失路径

> **环检测（必要）**：进入本步前先检查当前变更 proposal.md 的 `depth` 字段。
>
> - 如果当前 `depth >= 2`：不得再创建嵌套 fix 变更。定位到最上游的 parent-change，请用户直接处理根问题。
> - 创建新 fix 变更时，必须写 `parent-change: <当前变更名>` 和 `depth: <父 depth + 1>`。

1. 在 `.ai/L3-specs/changes/` 下创建或复用 fix 变更（如 `fix-empty-password-validation`）
2. 写 `proposal.md`（Why: bug 描述；What: spec 修正；parent-change/depth 必填）
3. 写 delta spec：
   - 缺失 → `## ADDED Requirements`
   - 歧义 → `## MODIFIED Requirements`，用明确的 WHEN/THEN 消除歧义
4. **展示 delta spec 给用户确认** — 这是一次额外的轻确认（不是完整的门槛 1，但因为 spec 变更是业务决策，必须人确认）
5. 确认后 → 按新 spec 继续走 Step 4B（改测试）→ Step 4A（改代码）

### Step 5: 更新追溯 & 状态回流

1. 更新 `.ai/L5-validation/traceability/<domain>.md` — 该 Scenario 改为 ✅ verified
2. 根据 Step 1 识别的场景，回写变更状态：

| Step 1 场景 | proposal.md 状态 |
|:-----------|:-----------------|
| Review 打回 | `review-failed` → `implementing` → 修完 → `pending-review` |
| 虚假通过 | `review-failed` → `implementing` → 修完 → `pending-review` |
| 开发中挂了 | 保持 `implementing` |
| 已归档功能 bug | 新建 fix 变更；如仅修代码可直接进入 `implementing`，如需补 spec 则先走 `drafting` → `implementing` |

3. 更新 `.ai/L4-session/active-session.md`

### Step 6: 输出报告

```
## Bug 修复完成

**触发场景**: [review 打回 / 开发中测试挂 / 已归档 bug / 虚假通过]
**根因分类**: [A 代码 Bug / B 测试 Bug / C 虚假通过 / D Spec 歧义 / E Spec 缺失]
**根因描述**: [具体原因]

**变更内容**:
- Spec: [有/无变更，如有列出 delta]
- 测试: [新增 N / 修改 N]
- 代码: [修改的文件]

**测试结果**: ✅ 全部通过 / ❌ 仍有失败
**变更状态**: [变更名] → [新状态]

### 受影响的 Requirement
| Requirement | Scenario | 修复前 | 修复后 |
|-------------|----------|--------|--------|
```

### Step 7: 循环出口提示（单次结束）

本次调用到此结束。**不要自动继续修下一个 bug**。输出如下循环提示供外层调度器使用：

```
## 循环状态
- 本次已修复: [bug 描述]
- 本次结果: [✅ 修复完成 / ⚠️ 部分修复 / ❌ 未修复]
- 队列剩余: [N 个 bug]
- 下次调用将修: [下一个 bug 描述，或"队列空"]
```

> **定时任务接入**：外层 scheduler 每次调用本 Skill，读取"下次调用将修"字段作为下次 argument；当输出"队列空"时停止循环。

## 反模式（禁止）

- ❌ 单次调用修复多个 bug（违反循环设计；每次只修一个）
- ❌ 没跑测试就开始改代码
- ❌ 跳过分诊直接改代码（"看起来像代码问题"）
- ❌ 虚假通过场景下只加日志不改测试（测试依旧过不了新 assertion）
- ❌ Spec 歧义场景下不改 spec 就直接改代码（下次又会被人踩）
