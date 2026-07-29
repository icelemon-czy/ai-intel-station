---
name: init-project
description: "从零创建一个可运行、经过测试并已配置 Compass 的新项目。Use only for greenfield or new-project requests; not for adding features to an existing repository."
---

# Init Project（从零到可开发）

从用户的一句话出发，完成：需求澄清 → 技术选型 → 项目脚手架 → `.compass/` 安装与上下文 → 第一个 Spec。

> 用户只负责会改变产品方向的决策。可从请求、代码或常见安全默认值确定的内容由 Agent 直接完成，并把必要问题合并成一次确认。

## Prerequisites

- 用户描述了想做什么（可以很粗略，如"我想做一个 XX"）
- 当前工作目录是目标项目根目录，用户已将 Compass 的 `compass/` 复制为该目录下的 `.compass/`
- 除 `.compass/`、用户提供的初始文档和可选 Git 元数据外，当前目录尚未包含已有应用实现

## Procedure

### Step 0: 验证当前项目根目录

1. 将当前工作目录视为唯一的目标项目根目录，确认 `.compass/INSTALL.md` 存在。
2. 若不存在，在任何需求分析或脚手架操作前停止，请用户先创建空项目目录并把 Compass 复制为 `.compass/`；不从不明确位置拼装文件。
3. 检查已有文件和 Git 状态。发现已有应用代码时，这不是 greenfield 初始化；保留用户内容并转为 `develop` 或其他匹配目标，不覆盖。
4. 后续步骤只在当前根目录内原地初始化；不再创建同名嵌套项目目录，不移动 `.compass/`。

---

### Phase A: 需求澄清 + 技术选型

#### Step 1: 需求澄清

通过用户描述按以下维度提炼。缺失内容先判断能否采用低风险默认值；只有答案会改变产品范围、数据、安全、部署或主要成本时才询问：

| 维度 | 要提取的信息 | 示例 |
|:-----|:------------|:-----|
| 项目目标 | 一句话概括做什么、给谁用 | "给内部团队用的报表系统" |
| 功能性需求 | 3-7 个核心功能点 | 登录、报表生成、CSV 导出 |
| 用户角色 | 有哪些角色，权限有何不同 | admin、viewer |
| 非功能需求 | 性能、安全、可用性 | "支持 100 并发"、"需要 HTTPS" |
| 部署约束 | 本地/云/容器/Serverless | "部署到 AWS Lambda" |
| 集成约束 | 第三方 API、已有系统 | "对接公司 SSO" |
| 数据约束 | 数据量级、存储、合规 | "日增 10 万条"、"需要 GDPR 合规" |

将所有真正阻塞的问题合并成一批，不逐项审问，不询问读现有材料或运行检查即可知道的事实。

#### Step 2: 技术选型建议

根据需求给出一个有理由的默认技术方案。只有两个方案会产生实质性产品、运维或成本差异时，才列出简短 pros/cons 让用户选择；用户已指定技术栈时直接采用。

| 维度 | 要给出的建议 |
|:-----|:-------------|
| 语言 + 框架 | 主要语言、Web 框架、ORM 等 |
| 数据存储 | 数据库类型 + 具体选择 |
| 项目结构 | 目录布局方案 |
| 测试框架 | 单测 + 集成测试工具 |
| 构建 + 部署 | 包管理、构建工具、CI 建议 |

**需要选择时的对比格式**：

```
| 维度 | 方案 A: [名称] | 方案 B: [名称] |
|:-----|:--------------|:--------------|
| 语言+框架 | Node + Express | Go + Gin |
| 优势 | 生态成熟、前后端同语言 | 高性能、强类型 |
| 劣势 | 单线程、类型安全弱 | 学习曲线、生态较小 |
| 适合场景 | 快速原型、全栈团队 | 高并发、系统编程 |
| 推荐度 | ⭐⭐⭐ | ⭐⭐⭐⭐ (因为需求中有"100并发") |
```

如果用户已指定技术栈，直接采用，只补充未指定的部分（无需对比）。

#### Step 3: 展示方案，必要时确认

向用户展示：

```
## 项目方案

**项目名称**: <name>
**一句话**: <what it does>

### 核心功能
1. ...
2. ...

### 技术选型
- 语言: ...
- 框架: ...
- 数据库: ...
- 测试: ...

### 需要确认
1. [如有未确定的业务问题]
```

存在会实质改变产品方向、数据、安全、部署或主要成本的未决项时，停下来等待一次确认。请求已经足够明确时，简短展示采用的方案并直接继续。

---

### Phase B: 脚手架搭建（自动）

#### Step 4: 在当前根目录初始化项目

根据确认的方案，在 Step 0 确认的当前项目根目录中原地执行初始化：

1. 运行支持当前目录的脚手架命令（`npm init`、`cargo init`、`go mod init` 等）。
2. 脚手架拒绝在含 `.compass/` 的非空目录运行时，在系统临时目录生成脚手架，检查输出后将应用文件非破坏地合并到当前根目录；不覆盖用户文件，不复制、移动或删除 `.compass/`。
3. 安装核心依赖（含测试框架）。
4. 创建基础目录结构和 `.gitignore`。
5. 初始化 git（如尚未初始化）。

> 此阶段 **不写业务代码**，只搭骨架。业务代码在 Phase D 用 TDD 方式写。

---

### Phase C: 初始化 Compass 上下文 + Spec（自动）

#### Step 5: 安装 Compass

Step 0 已确认 `.compass/INSTALL.md` 位于当前项目根目录。读取并执行该文件：

- 由每个已选 platform installer 非破坏地安装该平台的必读 instructions。
- 直接在已复制的 `.compass/context/` 中填写 L1–L5，已有内容不覆盖，也不创建第二个 context 目录。
- 由每个已选 platform installer 将 `.compass/skills/` 中的 installation source 安装到该平台的 project-level native directory。
- 根据用户选择逐个执行 `.compass/platforms/<platform>/INSTALL.md`。
- 由平台安装器自动渲染只读 `sdd-reviewer`；用户不需要选择或编排。`codebase-explorer` 只有明确要求时才额外安装。
- 如果项目位于 Git worktree，将 `/.compass/`、已选 platform 的根 `AGENTS.md` / `CLAUDE.md`、每个 Compass Skill 和 generated Subagent 精确 path 写入 local `info/exclude` 受管区块。

#### Step 6: 记录最小 L1 — 只写脚手架事实

读取 `.compass/context/L1-codebase-map/` 下的 `overview.md`、`architecture.md`、`module-map.md` 和 `key-files.md`。此时尚无业务实现，只记录能从已生成文件直接确认的事实：

- `overview.md` 只记录项目身份、真实技术栈和已存在的运行/测试入口。
- `architecture.md`、`module-map.md` 和 `key-files.md` 只写已存在的脚手架、基础设施和可执行命令。
- 不为尚未实现的核心功能创建 `features/<name>/README.md`，不猜测文件路径、数据流或模块依赖。
- 计划中的产品能力只写入 Step 8 的 L3 Spec；L1 只表达当前已存在的代码。

#### Step 7: 构建 L2 — 编码规则

- `L2-rules/global.md` — 根据技术选型生成编码规则
- `L2-rules/testing.md` — 根据测试框架生成测试规范
- `L2-rules/templates.md` — 代码模板（基于项目约定）

#### Step 8: 构建 L3 — 需求 Spec

读取 `.compass/context/L3-specs/specs/_capability-template/spec.md` — 了解 Requirement + Scenario 的格式要求。然后：

- `L3-specs/specs/system.md` — 系统级需求（TOR），从 Step 1 的需求澄清直接映射
- 为每个核心功能创建能力域 spec：`L3-specs/specs/<domain>/spec.md`
  - 每个 Requirement 至少 1 个 WHEN/THEN Scenario

#### Step 8.5: 只读 SDD plan review

`sdd-reviewer` 可用时以 `mode=plan` 检查系统边界、能力域冲突、Scenario 可观察性和验证面；Main Agent 复核引用并修正技术问题。只有发现会改变产品行为的歧义才询问用户；角色不可用时按同一检查 inline fallback。

#### Step 9: 构建 L5 — 初始追溯矩阵

- `L5-validation/traceability/` — 初始追溯矩阵（Spec ↔ Code ↔ Test），此时 Code/Test 列为空

#### Step 10: 验证安装边界

按 `.compass/INSTALL.md` 验证：当前根目录仍是 `.compass/` 的父目录且没有嵌套项目根、每个已选 platform 的必读 instruction file 保留原规则并包含最新受管区块、每个 project-level native Skill directory 都已安装完整 Skill 且没有 installer metadata file、没有 Skill 软链接、每个已选 platform installer 均返回结果，且 `sdd-reviewer` 已生成或明确记录 inline fallback。Git worktree 还要确认 local `info/exclude` 受管区块覆盖 `/.compass/`、已选 platform 根 instruction、Compass Skills 和 generated Subagents，且没有修改 shared `.gitignore`。同时确认 L1 只记录真实脚手架，没有把 L3 中计划的能力写成已实现功能。

---

### Phase D: TDD — 基于 Spec 写第一批代码（自动）

#### Step 11: 从 Spec Scenario 写测试

读取 `.compass/context/L2-rules/testing.md` — 遵守项目测试规范。

对 L3 中每个核心能力域的 Scenario，写测试：

- **WHEN** → 测试的 setup + action
- **THEN** → 测试的 assertion
- 优先覆盖 happy path，再覆盖关键 edge case

**运行测试，确认全部失败（红灯）。**

#### Step 12: 实现代码

让测试通过：

1. 创建入口文件（`main.ts`、`app.py`、`main.go` 等）
2. 按 `L2-rules/global.md` 编码规则实现
3. 创建新文件 → 查 `L2-rules/templates.md`
4. **运行测试，确认全部通过（绿灯）**

#### Step 13: Review、同步上下文与追溯矩阵

1. Main Agent 运行相关测试并保存实际结果；按 `L5-validation/validation-rules.md` 检查 Scenario、assertion、生产调用链和 false pass。
2. `sdd-reviewer` 可用时以 `mode=verify` 做只读复核。技术问题由 Main Agent 修复并重新验证；不可用时 inline fallback。
3. Review `PASS` 后读取 `.compass/context/L1-codebase-map/features/_feature-template/README.md` 和 `.compass/context/doc-sync.md`。根据 Phase D 真实存在的生产代码与测试（包括 greenfield 中尚未纳入 Git diff 的新文件）完成 L1：为已实现能力创建 feature 文档，并从实际调用链更新 overview、architecture、module-map 和 key-files。
4. 按 `doc-sync.md` 同步实际代码命中的其余 L1/L2，再次确认 L1 不包含未实现的计划功能；不要求用户另行触发上下文更新。
5. 更新 `L5-validation/traceability/`；只有实际核实的 Scenario 标为 ✅ verified。

---

### Phase E: 验证与交付

#### Step 14: 展示完成状态

向用户展示：

```
## 项目初始化完成

**项目**: <name>
**位置**: <path>

### 已创建
- [x] 项目脚手架 + 依赖安装
- [x] 已选 platform 的必读 instructions + .compass/context/
- [x] 已选 platform 的 project-level native directory 已安装 Compass Skills
- [x] Git local exclude 已覆盖全部 Compass installation path（非 Git 项目为 not applicable）
- [x] 基于 Spec 的测试（红灯 → 绿灯）
- [x] 追溯矩阵已更新

### Compass 概览
- AGENTS.md: 唯一项目规则
- skills: 9 个权威 Skill（7 个核心入口 + 可选 ralph-loop、skill-creator）
- subagents: sdd-reviewer（只读；不可用时 Main Agent inline fallback）
- L1: overview.md + N 个 feature 文档
- L2: global.md + testing.md + templates.md
- L3: system.md + N 个能力域 spec
- L5: 追溯矩阵（N 个 Scenario ✅）

### 建议的下一步
- 直接描述下一个目标，由 `/develop` 完成规划、实现、review 和归档
```

展示实际验证结果后完成，不再设置纯流程性的第二次确认。
