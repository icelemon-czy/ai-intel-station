# Project Compass Skill 工作流分析

> 盘点全部 Skill + 逐个展开 workflow + 全局工作流 + 已修缺口记录。

---

## 零、已修复的缺口（历史记录）

### 第一轮（v0.3.0）

| # | 原缺口 | 补丁 | 落地文件 |
|:--|:-------|:-----|:---------|
| 1 | `/spec-fix` 只面向"已归档 bug"，边界模糊 | 重命名 → `/fix-bug`，统一修复入口，含 5 类分诊（代码/测试/虚假通过/Spec歧义/Spec缺失） | `.github/skills/fix-bug/SKILL.md` |
| 2 | `/review-tests` 只做静态比对，不跑测试 | 新增 Step 0 强制跑测试，红灯自动转 `/fix-bug` | `.github/skills/review-tests/SKILL.md` |
| 3 | 没有"虚假通过"审查 | `/review-tests` Step 3 加入 7 条反模式清单 | 同上 |
| 4 | 状态机不完整，没有 `review-failed` | `_change-template/proposal.md` 加状态机图 + `Review Feedback` + `Known Gaps` 区段 | `L3-specs/changes/_change-template/proposal.md` |
| 5 | 宣传"唯一人工门槛"不准确 | 本文档第六节明确列出**两个人工门槛** | 本文档 |

### 第二轮（Skill 算法具体化）

| # | 原缺口 | 补丁 | 落地文件 |
|:--|:-------|:-----|:---------|
| 6 | `/review-tests` "抽样验证"导致虚假通过漏检 | 完全重写：穷举主表、调用链验证、反向推理、覆盖缺口分析、确定性判定规则（9 步流程） | `review-tests/SKILL.md` |
| 7 | 所有 Skill 的检查步骤只描述 WHAT 不描述 HOW | 11 个 Skill 全部加入具体检测算法/操作命令/判定条件 | 见下方明细 |
| 8 | `/git-commit` doc-sync 判断无具体规则 | 新增 5 条命中规则表（按变更类型→需同步文档映射） | `git-commit/SKILL.md` |
| 9 | `/check-changes` "很久未推进"无量化 | 量化为 > 7 天 + git log 检测命令 | `check-changes/SKILL.md` |
| 10 | `/setup-testing` "取最常见的"无算法 | 三级优先级（config > 依赖 > grep 统计）；[待确认]限 3 个且附原因 | `setup-testing/SKILL.md` |
| 11 | `/init-project` 需求提取主观 | 7 维度 checklist + 技术选型至少 2 方案 pros/cons 对比 | `init-project/SKILL.md` |
| 12 | `/new-change` 问题生成无维度 + L2 规则只列不查 | 问题来自 6 维度；Step 7 新增 L2 合规自检表 | `new-change/SKILL.md` |
| 13 | `/continue-change` "代码是否存在"无操作 | grep + 命中 0 行 = 不存在 | `continue-change/SKILL.md` |
| 14 | `/fix-bug` 分诊靠感觉 + 补 edge case 无方法 | Q1→Q6 决策树 + 边界值识别表 | `fix-bug/SKILL.md` |
| 15 | `/archive-change` "确认 verified"无依据 + "语法完整"无规则 | 必须有 review-tests 报告；5 条结构完整性规则 | `archive-change/SKILL.md` |
| 16 | `/build-ai` Verify 只是 checkbox | 替换为可执行 bash 验证脚本 | `build-ai/SKILL.md` |
| 17 | `/update-ai` Step 4 "update accordingly" | 5 个子步骤全部改为 diff 对比 + 具体增删操作 | `update-ai/SKILL.md` |

---

## 一、Skill 全景（13 个）

### 1. 项目初始化（4）

| Skill | 用途 |
|:------|:-----|
| `/git-init` | 新仓库初始化 |
| `/init-project` | 从零新项目：需求→选型→脚手架→.ai→首批 TDD |
| `/build-ai` | 已有代码，首次引入 `.ai/` |
| `/setup-testing` | 生成 / 更新 `L2-rules/testing.md` |

### 2. 需求开发（2）

| Skill | 用途 |
|:------|:-----|
| `/new-change` | 新功能：Proposal → Delta Spec → TDD |
| `/continue-change` | 接续未完成的变更 |

### 3. 审核归档（3）

| Skill | 用途 |
|:------|:-----|
| `/review-tests` | 跑测试 + 覆盖审查 + 虚假通过狩猎 |
| `/archive-change` | 合并 delta → 移到 `archive/` |
| `/check-changes` | 看所有变更状态 |

### 4. 修复（1，替换原 /spec-fix）

| Skill | 用途 |
|:------|:-----|
| `/fix-bug` | 任何"不对劲"的统一入口：自动分诊 + 按类型修复 |

### 5. 文档维护（2）

| Skill | 用途 |
|:------|:-----|
| `/update-ai` | 代码改了后增量刷新 `.ai/` |
| `/git-commit` | 生成 commit message + doc-sync 检查 + push |

---

## 二、每个 Skill 的内部 Workflow

### 2.1 `/git-init`

```
输入: 空目录 / 已有代码
  ↓
创建 .gitignore / README 模板
  ↓
git init → git add → git commit (first commit)
  ↓
可选: 配置 remote (github/gitlab)
  ↓
输出: 干净的 git 仓库
```

### 2.2 `/init-project`

```
Phase A: 需求澄清 + 技术选型        ✋ 人工确认
  ↓
Phase B: 脚手架（不写业务代码）
  ↓
Phase C: 构建 .ai/（L1/L2/L3/L5）+ 写初始 Spec
  ↓
Phase D: 按 Spec 做 TDD
   ├─ 从 Scenario 写测试 → 红灯
   └─ 实现代码 → 绿灯 → 更新追溯
  ↓
Phase E: 展示完成状态              ✋ 人工检查
```

### 2.3 `/build-ai`

```
扫描代码库 → 识别模块 / 功能
  ↓
构建 L1 (overview / features / key-files / module-map)
  ↓
构建 L2 (global / testing / templates)
  ↓
构建 L3 (system.md + 各 domain spec.md)
  ↓
构建 L5 追溯矩阵骨架
  ↓
部署 entrypoint（clinerules.md 等）
```

### 2.4 `/setup-testing`

```
扫描测试文件 / 依赖 → 识别框架 (jest/pytest/go test/...)
  ↓
提取项目已有测试约定（命名 / 目录 / mock 策略）
  ↓
生成 / 更新 L2-rules/testing.md
  ↓
产出: 测试规范 + 反模式清单
```

### 2.5 `/new-change`

```
Step 1: 收集上下文 + 定位功能模块
  ↓
Step 2: 写 proposal.md (状态=implementing)
  ↓
Step 3: 展示 Proposal + 业务问题        ✋ 人工门槛 1：业务确认
         问题来自 6 个维度：范围/边界/错误处理/并发/兼容/迁移
  ↓
Step 4: 生成 Delta Spec（ADDED/MODIFIED/REMOVED Requirements）
  ↓
Step 5: 生成 tasks.md（第一组固定为 Tests）
  ↓
Step 6: TDD — 从 Scenario 写测试 → 红灯
  ↓
Step 7: 实现代码 → 绿灯
   ├─ 写代码前：强制读取 L2 规则，明列 3-5 条关键规则
   └─ 写代码后：L2 合规自检表（逐条 ✅/🔴，有 🔴 先修）
  ↓
Step 8: 更新 L5 追溯 → 状态改为 pending-review
  ↓
提示用户: 运行 /review-tests
```

### 2.6 `/continue-change`

```
读 .ai/L4-session/active-session.md → 确定断点
  ↓
读对应变更的 proposal.md + tasks.md → 找到下一步
  ↓
根据当前状态恢复上下文：
  drafting → 继续 /new-change
  implementing → 继续 TDD
  review-failed → 读 Review Feedback → 转 /fix-bug
  pending-review → 提示用户 /review-tests
  approved → 提示用户 /archive-change
```

### 2.7 `/review-tests`（已改造 — 深度重写版）

```
Step 0: 跑测试 + 扫描异常标记（.skip/.only/pending）
  ├─ 红灯 → 立即转 /fix-bug，结束
  ├─ .only → 🔴 高风险（其他测试被静默跳过）
  └─ 全绿且无异常 → 继续
  ↓
Step 1: 确定审查范围 + 收集完整 Scenario 清单
         初始化"主表"（每行 = 一个 Spec Scenario，后续步骤逐列填充）
         列: Req | Scenario | Spec THEN | 测试函数 | 实际 assertion | 调用链 | 反模式 | 反向推理 | 结论
  ↓
Step 2: 逐 Scenario 定位测试（穷举，非抽样）
  ├─ 2a: 逐字摘抄 Spec THEN（不改写不概括）
  ├─ 2b: 定位测试函数（traceability → grep → 找不到 = ❌ 缺失）
  └─ 2c: 逐 assertion 比对 vs Spec THEN（检查存在性 / 对齐度 / 强度）
  ↓
Step 3: 【新增】调用链验证（防 Mock 架空）
  ├─ 3a: 从测试反向追踪到被测入口函数
  └─ 3b: 确认被测函数是真实代码（mock 外部依赖 ✅ / mock 被测函数本身 🔴）
         + 检查 test data 是否触发 Spec WHEN 条件
  ↓
Step 4: 虚假通过狩猎（7+N 条反模式，逐测试函数逐条标注 ✅/🔴）
  ├─ 每条有具体检测算法（不是只看信号）
  └─ 项目自定义反模式从 L2-rules/testing.md 追加
  ↓
Step 5: 【新增】反向推理 —"删掉代码还能绿吗？"
         对每个关键 assertion 做阅读级推理
  ├─ 会变红 → ✅ 测试有效
  ├─ 不会变红 → 🔴 测试无效
  └─ 不确定 → ⚠️ 需人工复核
  ↓
Step 6: 【新增】覆盖缺口分析
  ├─ 6a: 代码分支无对应 Scenario → 建议补 spec + 补测试
  └─ 6b: 边界值检查（空串/0/负数/null/超限）→ 登记缺失边界
  ↓
Step 7: 输出审查报告
  ├─ 主表（每行每列必填，空列 = 缺陷）
  ├─ 覆盖概要 / 反模式统计 / 覆盖缺口
  └─ 结论（确定性规则，不允许 AI 自由裁量）：
     有任何 🔴 或 ❌ → 打回
     只有 ⚠️ → 有缺口但非阻塞
     全部 ✅ → 通过
  ↓
Step 8: 状态回流
  ✅ → pending-review → approved，提示 /archive-change
  ❌ → pending-review → review-failed，提示 /fix-bug
  ⚠️ → 登记到 Known Gaps，并推进到 approved
```

### 2.8 `/fix-bug`（新，替换 /spec-fix）

```
Step 0: 场景识别（看 changes/ 状态确定触发场景）
  ↓
Step 1: 定位 spec + feature 文档
  ↓
Step 2: 跑测试 + 按决策树分诊（Q1→Q6 逐步排查，非整体感觉）
  Q1: 有测试失败吗？
  ├─ 是 → Q2: 找到对应 Spec WHEN/THEN？
  │   ├─ 是 → Q3: assertion 和 THEN 说的同一件事？
  │   │   ├─ 是 → A. 代码 Bug → Step 3A
  │   │   └─ 否 → B. 测试 Bug → Step 3B
  │   └─ 否 → E. Spec 缺失 → Step 3C
  └─ 否（全绿但行为错）→ Q4: Spec 中有对应 THEN？
      ├─ 是 → C. 虚假通过 → Step 3B
      └─ 否 → D/E. Spec 歧义或缺失 → Step 3C
  ↓
Step 3A 改代码 → 测试由红转绿
Step 3B 改/加测试（含边界值表识别 edge case）→ 确认能捕获问题（必须见红灯）
Step 3C 新建/复用 fix 变更 → delta spec → ✋ 确认 → 回 3B → 3A
         （环检测：depth >= 2 禁止再嵌套，回溯到 parent-change）
  ↓
Step 4: 更新 L5 追溯 + proposal 状态回流（review-failed → implementing → pending-review）
  ↓
Step 5: 输出报告（触发场景 / 根因分类 / 变更状态）
```

### 2.9 `/archive-change`

```
前置检查: 变更状态 == approved
  ↓
合并 Delta Spec 到 specs/<domain>/spec.md
  ├─ ADDED → 追加
  ├─ MODIFIED → 替换
  └─ REMOVED → 删除
  ↓
移动 changes/<name>/ → archive/YYYY-MM-<name>/
  ↓
更新 L5 追溯（状态改为 ✅ verified）
  ↓
更新 proposal.md 状态 → archived
  ↓
提示: /update-ai + /git-commit
```

### 2.10 `/check-changes`

```
ls .ai/L3-specs/changes/ → 所有进行中变更
ls .ai/L3-specs/archive/ → 历史归档
  ↓
读每个 proposal.md 的状态 + 修改时间
  ↓
输出看板:
  | 变更 | 状态 | 创建时间 | 最近更新 | 下一步动作 |
```

### 2.11 `/update-ai`

```
git diff HEAD~N → 识别变更的代码文件
  ↓
对照 .ai/doc-sync.md 的同步规则
  ↓
触发的文档层：
  ├─ 新增/删除模块 → L1 (overview + features)
  ├─ 新编码模式 → L2 (global / testing / templates)
  └─ 接口契约变 → 相关 feature 的 README
  ↓
增量更新对应文件
  ↓
输出: 本次同步了哪些文档
```

### 2.12 `/git-commit`

```
Step 1: git status + git diff HEAD → 总结变更
  ↓
Step 1.5: README 检查（非 README 变更但 README 没改 → 警告）
  ↓
Step 2: doc-sync 检查（.ai/doc-sync.md → 是否触发 L1/L2 同步）
  ↓
Step 3: git add -A → commit → push (带 proxy)
  ↓
输出: commit hash + branch
```

---

## 三、状态机（修正后）

```
drafting ──→ implementing ──→ pending-review ──→ approved ──→ archived
   ↑              ↑ ↑              │
   │              │ └──────────────┘
   │              │   review 打回
   │              │   (review-failed → implementing)
   │              │
   └──────────────┘
     spec 歧义回退（走 /fix-bug Step 3C）
```

| 状态 | 进入条件 | 下一状态 | 谁推进 |
|:-----|:--------|:---------|:-------|
| `drafting` | `/new-change` 启动 | `implementing`（业务确认后） | 人 |
| `implementing` | Proposal 确认 / review 打回 | `pending-review`（绿灯后） | AI |
| `pending-review` | TDD 完成 | `approved` / `review-failed` | AI → Reviewer |
| `review-failed` | `/review-tests` 打回 | `implementing`（走 /fix-bug） | Reviewer → AI |
| `approved` | Review 通过 | `archived`（归档后） | Reviewer |
| `archived` | `/archive-change` 完成 | — | AI |

---

## 四、完整工作流（修正版）

```
┌────────────────────────────────────────────────────────────┐
│ 项目启动（一次性）                                            │
│  /git-init → /init-project 或 /build-ai → /setup-testing    │
└────────────────────────────────────────────────────────────┘
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 日常开发循环                                                  │
└────────────────────────────────────────────────────────────┘
                         ↓
                   /new-change
                         ↓
             Proposal ──✋ 人工门槛 1：业务确认
                         ↓
              Delta Spec → 红灯测试 → 绿灯代码
                         ↓
                  pending-review
                         ↓
                  /review-tests
              （跑测试 + 覆盖审查 + 虚假通过狩猎）
                         ↓
           ┌─────────────┼─────────────┬──────────────┐
           ↓             ↓             ↓              ↓
        ❌ 测试红      ✅ 全绿齐全    ⚠️ 覆盖不足    ⚠️ 虚假通过
           ↓             ↓             ↓              ↓
       /fix-bug     ✋ 门槛 2      登记 Known     /fix-bug
                (自动分诊)   → approved      Gaps → approved  (Step 3B)
                     ↓             ↓
                   修完回到       /archive-change
                 pending-review           ↓
                   /update-ai + /git-commit
                            ↓
                    → 下一个 /new-change

┌────────────────────────────────────────────────────────────┐
│ 辅助 Skill（随时触发）                                        │
│   /continue-change — 接续昨天的工作                           │
│   /check-changes   — 看所有变更进度                           │
│   /fix-bug         — 任何时候发现问题                         │
│   /git-commit      — 提交代码                                │
└────────────────────────────────────────────────────────────┘
```

---

## 五、Skill 之间的调用关系

```
/new-change ──→ pending-review ──→ /review-tests
                                      │
                         ┌────────────┼────────────┐
                         ↓            ↓            ↓
         ✅ approved        ❌ /fix-bug   ⚠️ approved
          │                 │
       /archive-change          └──→ 回到 pending-review

/continue-change 会读状态机 → 自动判断该调 /new-change 还是 /fix-bug 还是 /review-tests

任何 skill 结束 → /git-commit 收尾
```

---

## 六、两个人工门槛

| 门槛 | 所在 Skill | 决策内容 | 典型耗时 |
|:-----|:----------|:---------|:---------|
| **1. Proposal 确认** | `/new-change` | 业务决策：这个需求要不要做、怎么做 | 几分钟 |
| **2. Review 批准** | `/review-tests` | 质量决策：测试够不够、有没有虚假通过、可不可以归档 | 几分钟到几十分钟 |

> 第 3 类（Spec 歧义时）会在 `/fix-bug` Step 3C 出现一次**临时门槛**，因为修 spec 本质上是业务决策。但这是例外情况，不是常规流程的固定门槛。

其余全部自动化：写 spec、写测试、写代码、分诊、修 bug、归档、同步文档、提交。

---

## 七、虚假通过反模式清单（Reviewer 必过）

这是 `/review-tests` Step 4 的核心检查表，**每条都要逐一过，每条必须标注 ✅ 通过 / 🔴 命中**：

| # | 反模式 | 检测算法（AI 必须按此操作） | 风险 |
|:--|:-------|:--------------------------|:-----|
| 1 | **断言缺失** | 在测试函数体内 grep `assert\|expect\|should\|verify`。数量 = 0 → 命中 | 🔴 |
| 2 | **断言太弱** | 列出所有 assertion。任何一个只做 `toBeTruthy()\|toBeDefined()\|toBeNotNull()\|!= null\|>= 0` 而不比对具体预期值 → 命中 | 🔴 |
| 3 | **Happy path only** | 统计该 Requirement 下所有 Scenario。只有 1 个正常路径 test，缺 edge/error path → 命中 | 🔴 |
| 4 | **Mock 了要测的东西** | 调用链验证（Step 3b）已检查。mock 被测函数本身 → 命中 | 🔴 |
| 5 | **Assertion 绕开 spec THEN** | 比对"Spec THEN"列和"实际 assertion"列。验证的不是同一件事 → 命中 | 🟡 |
| 6 | **条件永真** | `expect(x).toBe(x)` / `expect(true).toBe(true)` / 空 snapshot → 命中 | 🔴 |
| 7 | **吞异常** | try-catch 中 catch 块为空 / 只有 console.log / 没有 expect → 命中 | 🔴 |

> 第 8+ 条：项目可在 `.ai/L2-rules/testing.md` 的"自定义反模式"区段追加。前 7 条是底线，不可删除。

**每个测试函数的输出格式**：

```
| # | 反模式 | 结果 | 证据 |
|:--|:-------|:-----|:-----|
| 1 | 断言缺失 | ✅ 通过 | 2 个 expect |
| 2 | 断言太弱 | 🔴 命中 | `expect(result).toBeTruthy()` 应改为具体值 |
| ... | ... | ... | ... |
```

发现任何一条 🔴 → 打回 → `/fix-bug` Step 3B。
