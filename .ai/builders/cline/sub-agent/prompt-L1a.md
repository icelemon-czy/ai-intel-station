# Cline 构建 L1 代码导航文档 — Phase 1-3（发现阶段）

> **使用顺序**：先用本文件，完成后用 `prompt-L1b.md` 继续。
> 使用前替换 `[项目配置文件]`、`[项目目录]` 和 `[入口文件]` 为实际路径。
> **可选**：替换 `[补充上下文文件路径]` 为一个 `.md` 文件路径，模型会在 Phase 1 开始前读取它。
>
> **本文件产出**：overview.md + 功能清单 + `_handoff.md`（交接摘要）
> **下一步**：开新对话，使用 `prompt-L1b.md` 完成 Phase 4-5

---

## Prompt

```markdown
# 任务：构建项目代码导航文档（L1）— Phase 1-3

## 背景
我需要为本项目构建 AI 上下文文档中的 **L1 代码导航层**。

文件结构：
```
.ai/L1-codebase-map/
├── overview.md              ← 轻量索引（< 60 行），每次对话必读
├── architecture.md          ← 运行时架构（请求生命周期、启动顺序、运行时协作）
├── module-map.md            ← 模块合约与耦合，跨模块修改时加载
├── key-files.md             ← 通用任务食谱，做常见任务时加载
├── infrastructure/          ← 基础设施文档（与 features 平级）
│   ├── _infrastructure-template/  ← 内容格式参考
│   │   └── README.md
│   └── [组件名]/            ← 每个基础设施组件一个文件夹
│       ├── README.md        ← 组件概览 + 分层导航
│       └── [层名].md        ← 按组件层次拆分，按需加载
└── features/                ← 按功能拆分的详细上下文
    ├── _feature-template/   ← 内容格式参考（不要机械复制文件名）
    │   └── README.md        ← 功能概览 + 分层导航 + 层文件格式参考
    ├── user-auth/           ← 功能 1 的完整上下文
    ├── order-management/    ← 功能 2
    └── ...
```

**设计思路**：
- overview.md 只是一个索引表，告诉 AI "有哪些功能、入口在哪、详情在哪个文件"
- 收到任务时，AI 查索引 → 定位到一个功能 → **只加载那个功能文件**
- 这样无论项目多大，每次加载的上下文量都是可控的

## 补充上下文（可选）

<!-- 如果你有现成的 .md 文件（架构说明、团队规范、技术约束、领域术语表等），
     在这里指定路径，模型会在 Phase 1 之前先读取。不指定则跳过。 -->

如果提供了补充上下文文件，先执行：
```bash
cat [补充上下文文件路径]
```
将读取到的内容作为整个分析过程的额外背景知识。在 Phase 2 划分功能、Phase 3 写 overview 时都应参考。

## 核心原则
- ❌ 不要在 overview.md 里塞详情（数据流、涉及文件列表）— 那些放到 feature 文件
- ✅ overview.md 只做索引：功能名 + 一句话 + 指向 feature 文件的路径
- ❌ 不要写 AI 能从 tree/grep 推导出来的信息
- ✅ 要写 AI 从代码推导不出来的信息（数据流路径、变更联动、陷阱）
- ✅ 每个功能文件自包含：读了这一个文件就够做该功能相关的任务

## 你的工作步骤

### Phase 1: 快速收集原始信息（只用命令，不要逐文件阅读）

```bash
# 目录结构（3 层深度，排除常见生成目录）
find . -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/build/*' -not -path '*/target/*' | head -120 | sort

# 项目配置
cat [项目配置文件]

# 入口文件
cat [入口文件]

# README（如果有）
cat README.md

# Lint / 格式化配置（如果有）
cat .eslintrc* tsconfig.json .prettierrc* pyproject.toml setup.cfg .golangci.yml 2>/dev/null

# 构建/测试命令来源
cat Makefile 2>/dev/null; cat package.json 2>/dev/null | grep -A 30 '"scripts"'

# 找出所有 import/依赖关系
grep -rn "import\|from\|require" --include='*.ts' --include='*.py' --include='*.java' --include='*.go' | head -100

# 找出潜在陷阱
grep -rn "TODO\|FIXME\|HACK\|WARN\|DEPRECATED\|LEGACY" --include='*.ts' --include='*.py' --include='*.java' --include='*.go' | head -50

# 找出模块公开 API（export / __all__ / public）
grep -rn "^export\|module\.exports\|__all__" --include='*.ts' --include='*.py' --include='*.js' | head -80

# 测试文件分布
find . -name "*.test.*" -o -name "*_test.*" -o -name "test_*" | head -30

# 最近的 commit 模式
git log --oneline -20 2>/dev/null

# 分支命名模式
git branch -a 2>/dev/null | head -20
```

### Phase 2: 识别功能边界（仅做划分，不深入分析）

> **构建顺序**：先识别基础设施（地基），再识别功能（建在基础设施之上），最后识别跨功能模式。

#### 2a: 识别基础设施层

> **Infrastructure** = 被 ≥2 个 feature 共享的底层机制（如框架基类、配置系统、CI/CD、测试框架、通用工具等）。
> 只服务于单个 feature 的 helper → 归入该 feature 的层文件，不放 infrastructure。

**输出格式**：

| 基础设施组件 | 代表文件/目录 | 一句话说明 |
|---------------|----------------|------------|
| [如: 框架基类] | [src/framework/] | [DI 容器 + 基类体系] |

> 如果项目简单，没有明显的基础设施层，可以跳过本步"无基础设施层"。

#### 2b: 划分功能，输出功能清单
从 Phase 1 的信息中，识别项目的核心业务功能（通常 3-8 个）。

> **Feature** = 产品经理叫得出名字的业务能力（如"用户认证"、"订单处理"）。不是代码模块。

**输出格式（只输出这张表，不要在这里追踪数据流或分析细节）**：

| 功能名 | 疑似入口文件 | 追踪起点（函数/方法名） | 规模 | 一句话说明 |
|--------|-------------|----------------------|------|------------|
| user-auth | src/auth/routes.ts | Login() | medium | 用户登录/注册/token 刷新 |
| order-management | src/orders/handler.go | CreateOrder() | large | 订单创建、取消、查询 |
| config-loader | src/config/loader.go | Load() | small | 读取并合并配置文件 |

**规模说明**：
- `small` — 逻辑集中，README.md 一个文件即可
- `medium` — 有 2-3 个明显的层，需要分层文件
- `large` — 层次复杂或文件众多，需要完整分层 + 详细追踪

> ☸️ 主 agent 到此为止。每个功能的深入分析、数据流追踪、变更联动发现全部交给 subagents（Phase 4，在下一个文件中执行）。

#### 2c: 识别跨功能的通用模式
- 3-5 个相似实现 → 提取任务食谱（用于 key-files.md）
- 雷区（自动生成的文件、legacy 代码）
- 全局的变更影响（改配置文件 → 影响范围）

### Phase 3: 填写 overview.md（轻量索引）

读取 `.ai/L1-codebase-map/overview.md` 模板，填写：
- 项目身份（3 行）
- 架构约束（只写禁止的方向）
- **功能索引表**：每行一个功能，只有功能名 + 一句话 + 指向 feature 文件 + 入口文件
- **基础设施索引表**（与功能索引分开）：每行一个基础设施组件 + 一句话 + 指向 infrastructure 子目录
- 术语、雷区、构建命令

> ⚠️ 基础设施不要放进功能索引表，它们是不同的 section。

**控制在 60 行以内。不要在这里写数据流或详细文件列表。**

### Phase 4（交接）: 写入 _handoff.md

> ⚠️ **这是本文件的最后一步**，必须在 Phase 3 的 overview.md 写好后执行。
> 将以下信息写入 `.ai/L1-codebase-map/_handoff.md`，供下一个对话（Phase 4-5）使用。

文件内容格式：

```markdown
# L1 构建交接摘要

> 由 prompt-L1a.md 对话自动生成，供 prompt-L1b.md 对话读取。

## 基础设施层（Phase 2a）

<!-- 将 Phase 2a 识别出的基础设施组件表复制到这里。如果没有，写「无」。 -->

## 功能清单

| 功能名 | 入口文件 | 追踪起点 | 规模 | 一句话说明 |
|--------|---------|---------|------|------------|
<!-- 将 Phase 2b 的功能清单完整复制到这里 -->

## 跨功能通用模式（Phase 2c）

<!-- 将 Phase 2c 识别出的通用模式、任务食谱线索、雷区完整复制到这里 -->

## 补充上下文

<!-- 如果 Phase 1 之前读取了补充上下文文件，将其完整内容复制到这里。如果没有，写「无」。 -->

## overview.md 全文

<!-- 将刚写好的 overview.md 完整内容粘贴到这里 -->
```

写完后，提示用户：
**"Phase 1-3 完成。请开新对话，使用 `prompt-L1b.md`，并告知模型读取 `.ai/L1-codebase-map/_handoff.md`。"**

## 约束
- overview.md < 60 行，只做索引
- 每个 feature 文件自包含，可独立加载
- 不确定的地方写 `[待确认：xxx]`
- **检验标准**：每一行都问"AI 从代码中能推导出来吗？"如果能，删掉
```

---

## 补充说明

### 质量检验清单

| 检查项 | 通过标准 | 不通过的例子 |
|--------|----------|-------------|
| overview 是否轻量？ | < 60 行，只有索引 + 雷区 + 构建命令 | ❌ overview 里写了完整数据流 |
| _handoff.md 是否完整？ | 功能清单 + 跨功能模式 + overview 全文 | ❌ 只写了功能名，缺入口文件和追踪起点 |

### 完成后

写完 `_handoff.md` 后，**开新对话**使用 `prompt-L1b.md` 继续 Phase 4-5。
