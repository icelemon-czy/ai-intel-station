# Copilot 构建 L1 代码导航文档 — Phase 4-5（深入分析阶段）

> **前置条件**：已完成 `prompt-L1a.md`，且 `.ai/L1-codebase-map/_handoff.md` 已存在。
> **本文件产出**：features/[name]/ 完整文档 + architecture.md + module-map.md + key-files.md
>
> **与 Claude 版区别**：Copilot 无原生 subagent 机制，改为顺序逐功能分析，自动继续。

---

## Prompt

```markdown
# 任务：构建项目代码导航文档（L1）— Phase 4-5

## 准备工作

首先执行：
```bash
cat .ai/L1-codebase-map/_handoff.md
```

读取后，你将获得：功能清单、基础设施层（如有）、跨功能通用模式、补充上下文（如有）、overview.md 全文。这是本对话的全部背景。

---

> **构建顺序**：先建基础设施（地基），再逐个分析功能（建在基础设施之上）。

### Phase 4a: 填写基础设施文档（如有）

> 如果 `_handoff.md` 中「基础设施层」为「无」，跳过本步，直接进入 Phase 4b。
> ⚠️ **必须在 Phase 4b（功能分析）之前完成**，后续功能分析需要基础设施上下文。

根据 `_handoff.md` 中的基础设施组件表，填写 `.ai/L1-codebase-map/infrastructure/`：

#### Step 1 — 组件发现（先看代码，再输出清单）

对 `_handoff.md` 基础设施表中的每个组件，执行 `cat [代表文件]` 实际阅读代码。

阅读完后，输出组件清单：

| 组件名（项目词汇） | 代表文件 | 职责一句话 |
|------------------|---------|------------|
| [填写] | [填写] | [填写] |

**命名规则**：用项目里真实存在的概念（如 framework / config / plugin-host / logger / build-system / testing），禁止用抽象通用词。

> ⚠️ 未执行 cat 命令、未阅读实际代码前，不得进入 Step 2。

#### Step 2 — 追踪依赖关系 + 发现联动

分析每个组件：
- 哪些功能层使用了它？（grep import / require / from 的引用）
- 组件之间的依赖关系是什么？（如：插件系统依赖配置系统）
- 改了组件 A，哪些看似无关的东西也要改？
- 有 TODO/FIXME/HACK 的坑？

#### Step 3 — 创建文档文件

1. 读取模板：`cat .ai/L1-codebase-map/infrastructure/_infrastructure-template/README.md`
2. 参照模板格式，在 `.ai/L1-codebase-map/infrastructure/` 下创建实际文件：
   - 先更新 `README.md` — 填入组件索引表、架构全景、变更影响、已知陷阱
   - 为每个组件创建子文件夹 `[组件名]/`：
     - `README.md` — 组件概览 + 分层导航 + 关键文件 + 核心机制 + 对外接口
     - `[层名].md` — 如果组件内部有多层结构，按层拆分（简单组件只需 README.md 即可）

---

### Phase 4b: 逐个功能深入分析（核心步骤）

> 对 `_handoff.md` 功能清单里的**每个功能**，按以下流程顺序分析。
> 分析完一个功能后立即创建文件，然后继续下一个，**无需等待确认**。

对每个功能执行以下 3 步：

---

#### Step 1 — 层次发现（先看代码，再输出清单）

> 如果 `_handoff.md` 中有「补充上下文」，将其作为参考背景来识别层次和命名。

1. 执行 `cat [入口文件路径]` 阅读入口文件
2. 顺着调用链，对每一层的代表文件执行 `cat [文件路径]` 实际阅读
3. **阅读完代码后**，输出层次清单：

| 层名（项目词汇） | 代表文件 | 职责一句话 |
|----------------|---------|------------|
| [填写] | [填写] | [填写] |

**命名规则**：用项目里真实存在的概念（如 handler / service / repo / proto / worker），**禁止直接使用 entry / logic / data 通用词**。

> ⚠️ 未执行 cat 命令、未阅读实际代码前，不得进入 Step 2。

#### Step 2 — 追踪数据流 + 发现联动

以追踪起点函数为起点，追踪该功能最核心的 1-2 个操作的完整路径。
同时找出：
- 改了文件 A，哪些看似无关的文件 B 也要改？
- 有 TODO/FIXME/HACK 的坑？

#### Step 3 — 创建文档文件

在 `.ai/L1-codebase-map/features/[功能名]/` 下创建：

- `README.md` — **必须包含「分层导航」表**（每行对应一个层文件，写明加载时机和内容摘要），然后是数据流、变更影响表、已知陷阱
- `[层名].md` — 每层一个文件，详细记录该层的职责、关键文件、API、陷阱

README.md 中的「分层导航」表格式：
```markdown
## 分层导航
| 层文件 | 加载时机 | 包含内容摘要 |
|--------|---------|-------------|
| handler.md | 改 API 入口 / 加新端点时 | 路由注册、请求处理 |
| service.md | 改业务逻辑 / 加新规则时 | 核心规则、状态机 |
```

内容格式参考 `.ai/L1-codebase-map/features/_feature-template/README.md` 中的 section 结构和「层文件格式参考」部分，但文件名和文件数量完全由 Step 1 决定。

---

> 所有功能分析完成后，继续 Phase 5。

### Phase 5: 填写 architecture.md + module-map.md + key-files.md

使用 `_handoff.md` 中"跨功能通用模式"部分，结合各 feature 和 infrastructure 文档：

- **architecture.md** — 运行时架构：部署拓扑、请求生命周期、Feature ↔ Infrastructure 运行时协作表、启动顺序、中间件管道、错误传播路径、关键运行时配置
- **module-map.md** — 依赖拓扑（ASCII 全局依赖图）、模块公开 API、依赖规则、跨功能的变更联动
- **key-files.md** — 通用任务食谱（不属于单一功能的）、调查起点

> 💡 **依赖拓扑**：在 module-map.md 中生成一张 ASCII 依赖图，展示功能层 → 基础设施层的全局依赖关系。参考模板中的「依赖拓扑」部分。

## 约束
- 每个 feature 文件自包含，可独立加载
- 不确定的地方写 `[待确认：xxx]`
- **检验标准**：每一行都问"AI 从代码中能推导出来吗？"如果能，删掉
```

---

## 补充说明

### 质量检验清单

| 检查项 | 通过标准 | 不通过的例子 |
|--------|----------|-------------|
| feature 文件是否自包含？ | 只读这一个文件就够做该功能的任务 | ❌ 还要去 overview 查数据流 |
| README 是否有分层导航表？ | 每行对应一个层文件，写明加载时机 | ❌ README 没有导航表，AI 不知道该加载哪个分层文件 |
| 是否可推导？ | AI 不能从 tree + grep 快速推导出来 | ❌ "auth 模块在 src/auth/ 目录下" |
| 是否面向任务？ | 有具体的文件路径和步骤 | ❌ "改了 model 要更新相关文件" |
| feature 文件名是否反映实际架构？ | 文件名来自项目真实概念 | ❌ 所有功能都是 entry.md / logic.md / data.md |

### 完成后

L1 文档生成后，继续用 `prompt-L2.md` 生成 L2 编码规则。
建议在同一对话中继续（Phase 4-5 的信息可复用），或上下文满了就开新对话。
