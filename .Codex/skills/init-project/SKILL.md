---
name: init-project
description: "Initialize a new project from scratch: requirements → tech stack → scaffold → .ai context. Use when: 新项目, init project, 从零开始, start from scratch, 我想做一个, I want to build, 初始化项目, create project, 新建项目, bootstrap"
argument-hint: "Describe what you want to build (e.g., 'a TODO app with React', '一个博客系统用 Go')"
---

# Init Project（从零到可开发）

从用户的一句话出发，完成：需求澄清 → 技术选型 → 项目脚手架 → `.ai/` 上下文 → 第一个 Spec。

> **诚实声明**：本 Skill 的流程不是"一键生成"。需求澄清和技术选型本质上是对话，可能要停下来问你 **多次**（不止一两次）。主要的确认点是 Phase A（方案）和 Phase E（.ai 验收），但中间每当用户给的信息模糊时都会再问。其余能自动的都自动。

## Prerequisites

- 用户描述了想做什么（可以很粗略，如"我想做一个 XX"）
- project-compass 模板可用

## Procedure

---

### Phase A: 需求澄清 + 技术选型（需人确认）

#### Step 1: 需求澄清

通过用户描述，按以下 **checklist 逐项**提炼（不可跳过任何一项，用户未提到的标为"待确认"并主动询问）：

| 维度 | 要提取的信息 | 示例 |
|:-----|:------------|:-----|
| 项目目标 | 一句话概括做什么、给谁用 | "给内部团队用的报表系统" |
| 功能性需求 | 3-7 个核心功能点 | 登录、报表生成、CSV 导出 |
| 用户角色 | 有哪些角色，权限有何不同 | admin、viewer |
| 非功能需求 | 性能、安全、可用性 | "支持 100 并发"、"需要 HTTPS" |
| 部署约束 | 本地/云/容器/Serverless | "部署到 AWS Lambda" |
| 集成约束 | 第三方 API、已有系统 | "对接公司 SSO" |
| 数据约束 | 数据量级、存储、合规 | "日增 10 万条"、"需要 GDPR 合规" |

如果用户描述太模糊（checklist 中有 ≥3 项无法从描述中提取），提出澄清问题——问题**必须**来自上表中空白的维度，不要泛泛提问。

#### Step 2: 技术选型建议

根据需求推荐技术方案。**必须列出至少 2 个候选方案并附 pros/cons，让用户选择**（除非用户已明确指定技术栈）。

| 维度 | 要给出的建议 |
|:-----|:-------------|
| 语言 + 框架 | 主要语言、Web 框架、ORM 等 |
| 数据存储 | 数据库类型 + 具体选择 |
| 项目结构 | 目录布局方案 |
| 测试框架 | 单测 + 集成测试工具 |
| 构建 + 部署 | 包管理、构建工具、CI 建议 |

**候选方案对比格式**（至少 2 个方案）：

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

#### Step 3: 展示方案 → 等人确认

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

**停下来等待人类确认。这是第一个人工门槛。**

---

### Phase B: 脚手架搭建（自动）

#### Step 4: 初始化项目

根据确认的方案，执行项目初始化：

1. 创建项目目录
2. 运行对应的脚手架命令（`npm init`、`cargo init`、`go mod init` 等）
3. 安装核心依赖（含测试框架）
4. 创建基础目录结构
5. 创建 `.gitignore`
6. 初始化 git（如尚未初始化）

> 此阶段 **不写业务代码**，只搭骨架。业务代码在 Phase D 用 TDD 方式写。

---

### Phase C: 构建 `.ai/` 上下文 + Spec（自动）

#### Step 5: 复制 project-compass 模板

```bash
cp -r /path/to/project-compass /path/to/project/.ai/
```

#### Step 6: 构建 L1 — 代码导航

读取 `.ai/L1-codebase-map/` 下的模板文件（`overview.md`、`features/_feature-template/README.md`、`module-map.md`、`key-files.md`），了解期望格式，然后基于刚创建的项目结构填写：

- `L1-codebase-map/overview.md` — 功能索引（< 60 行）
- `L1-codebase-map/features/` — 按核心功能创建 feature 文档
- `L1-codebase-map/module-map.md` — 模块关系（初始版本）
- `L1-codebase-map/key-files.md` — 关键文件索引

#### Step 7: 构建 L2 — 编码规则

- `L2-rules/global.md` — 根据技术选型生成编码规则
- `L2-rules/testing.md` — 根据测试框架生成测试规范
- `L2-rules/templates.md` — 代码模板（基于项目约定）

#### Step 8: 构建 L3 — 需求 Spec

读取 `.ai/L3-specs/specs/_capability-template/spec.md` — 了解 Requirement + Scenario 的格式要求。然后：

- `L3-specs/specs/system.md` — 系统级需求（TOR），从 Step 1 的需求澄清直接映射
- 为每个核心功能创建能力域 spec：`L3-specs/specs/<domain>/spec.md`
  - 每个 Requirement 至少 1 个 WHEN/THEN Scenario

#### Step 9: 构建 L5 — 初始追溯矩阵

- `L5-validation/traceability/` — 初始追溯矩阵（Spec ↔ Code ↔ Test），此时 Code/Test 列为空

#### Step 10: 部署 Entrypoint

根据用户使用的 AI 工具，复制对应的 entrypoint：

| 工具 | 操作 |
|:-----|:-----|
| Claude Code | `cp .ai/entrypoints/claude.md ./CLAUDE.md` |
| Cline | `cp .ai/entrypoints/clinerules.md ./.clinerules` |
| GitHub Copilot | `mkdir -p .github && cp .ai/entrypoints/copilot-instructions.md ./.github/copilot-instructions.md` |

---

### Phase D: TDD — 基于 Spec 写第一批代码（自动）

#### Step 11: 从 Spec Scenario 写测试

读取 `.ai/L2-rules/testing.md` — 遵守项目测试规范。

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

#### Step 13: 更新追溯矩阵

更新 `L5-validation/traceability/` — 已实现的 Scenario 标为 ✅ verified。

---

### Phase E: 验证（需人检查）

#### Step 14: 展示完成状态

向用户展示：

```
## 项目初始化完成

**项目**: <name>
**位置**: <path>

### 已创建
- [x] 项目脚手架 + 依赖安装
- [x] .ai/ 上下文（L1 ~ L5）
- [x] Entrypoint 部署
- [x] 基于 Spec 的测试（红灯 → 绿灯）
- [x] 追溯矩阵已更新

### .ai/ 概览
- L1: overview.md + N 个 feature 文档
- L2: global.md + testing.md + templates.md
- L3: system.md + N 个能力域 spec
- L5: 追溯矩阵（N 个 Scenario ✅）

### 建议的下一步
1. 用 `/new-change` 开始下一个功能开发
2. 用 `/review-tests` 检查测试覆盖
```

**等待人类检查确认。这是第二个人工门槛。**
