---
name: ask-codebase
description: "Answer questions about the codebase: locate features, explain architecture, analyze change impact. Use when: 在哪, where is, 怎么工作, how does it work, 为什么这样设计, why designed this way, 改了会影响什么, what will break, 代码在哪, find code, 架构, architecture, 影响分析, impact analysis, explain, 解释"
argument-hint: "Your question about the codebase (e.g., '登录功能在哪', 'why is auth a separate module', '改 User 表会影响什么')"
---

# Ask Codebase — 代码库问答（定位 / 架构 / 影响分析）

> 用户对代码库有疑问时的统一入口。不做任何代码修改，只读取 `.ai/` 文档和源码来回答。

## 覆盖场景

| 场景 | 典型问题 | 主要数据源 |
|:-----|:---------|:-----------|
| **代码定位** | "登录功能在哪"、"CSV 导出的入口文件" | L1 overview → features/ |
| **架构解释** | "为什么 auth 是独立模块"、"请求生命周期是什么" | L1 architecture + module-map |
| **变更影响** | "改 User 表会影响什么"、"删掉这个接口安全吗" | L1 module-map（变更联动表）+ features/ |
| **规则查询** | "新建 Service 应该什么格式"、"错误处理规范" | L2 global + templates + module rules |
| **需求追溯** | "这个功能的 spec 在哪"、"谁要求加的这个功能" | L3 specs + archive |
| **测试定位** | "这个功能的测试在哪"、"哪些 Scenario 没测" | L5 traceability |

## Prerequisites

- `.ai/` 目录已存在且至少有 L1 层

## Procedure

### Step 1: 分类问题

读取用户问题，判断属于以下哪个类型（可能同时属于多个）：

| 类型 | 关键词信号 | 处理路径 |
|:-----|:----------|:---------|
| A: 代码定位 | "在哪"、"where"、"找到"、"入口"、"文件" | → Step 2A |
| B: 架构解释 | "为什么"、"怎么工作"、"设计"、"架构"、"流程" | → Step 2B |
| C: 变更影响 | "改了会"、"影响"、"删掉"、"break"、"安全吗" | → Step 2C |
| D: 规则查询 | "规范"、"怎么写"、"模板"、"约定"、"convention" | → Step 2D |
| E: 需求/测试追溯 | "spec"、"需求"、"谁要求"、"测试在哪"、"覆盖" | → Step 2E |

> 如果不确定类型，默认走 A（代码定位），因为大多数问题的根源是"找不到代码在哪"。

### Step 2A: 代码定位

1. 读取 `.ai/L1-codebase-map/overview.md` — 在功能索引中匹配用户问的功能
2. 匹配到 → 读取 `.ai/L1-codebase-map/features/<matched>/README.md` — 获取详细代码位置、层结构、数据流
3. 未匹配 → 读取 `.ai/L1-codebase-map/key-files.md` — 尝试从常见任务食谱中找到
4. 仍未找到 → 用 `grep -rn` 在源码中搜索关键词，给出文件位置

**输出格式**：

```
## 代码定位：[功能名]

### 入口
- 文件：`src/auth/routes.ts` (L45)
- 作用：处理 /login POST 请求

### 代码结构
| 层 | 文件 | 职责 |
|:---|:-----|:-----|
| 路由 | `src/auth/routes.ts` | 接收请求、参数校验 |
| 服务 | `src/auth/service.ts` | 业务逻辑（验证密码、生成 token） |
| 数据 | `src/auth/repository.ts` | 数据库查询 |

### 数据流
请求 → routes.ts:handleLogin() → service.ts:authenticate() → repository.ts:findUser() → 返回 token

### 相关文件
- 测试：`tests/auth/login.test.ts`
- Spec：`.ai/L3-specs/specs/auth/spec.md`
- 规则：`.ai/L2-rules/auth.md`
```

### Step 2B: 架构解释

1. 读取 `.ai/L1-codebase-map/overview.md` — 理解整体结构
2. 读取 `.ai/L1-codebase-map/architecture.md` — 获取运行时架构、请求生命周期、部署拓扑
3. 读取 `.ai/L1-codebase-map/module-map.md` — 理解模块间关系
4. 如果问题涉及具体功能 → 读取对应 `features/<name>/README.md`

**输出格式**：

```
## 架构解释：[问题摘要]

### 回答
[直接回答用户的问题，2-5 句话]

### 依据
| 来源文件 | 相关内容 |
|:---------|:---------|
| `architecture.md` | [引用的段落/图] |
| `module-map.md` | [引用的依赖关系] |

### 设计决策（如有历史记录）
- [从 archive/ 的 proposal.md 中找到的设计决策]

### 图示（如适用）
[用 ASCII 或 mermaid 画出相关架构片段]
```

### Step 2C: 变更影响分析

1. 读取 `.ai/L1-codebase-map/module-map.md` — **重点看"变更联动表"**，找到被改模块的下游影响
2. 读取被改文件所属功能的 `features/<name>/README.md` — 理解数据流和依赖
3. 如果涉及跨模块 → 读取所有相关模块的 `L2-rules/<module>.md` — 查看公开 API 合约（STABLE/INTERNAL 标记）
4. 用 `grep -rn` 搜索被改函数/类型的引用位置

**输出格式**：

```
## 变更影响分析：[改动描述]

### 直接影响
| 文件 | 影响原因 | 严重度 |
|:-----|:---------|:-------|
| `src/auth/service.ts` | 直接调用了被改函数 | 🔴 高 |
| `src/user/dto.ts` | 类型依赖 | 🟡 中 |

### 间接影响（传递依赖）
| 模块 | 路径 | 严重度 |
|:-----|:-----|:-------|
| payment | user → payment（通过 UserDTO） | 🟡 中 |

### API 合约检查
| 被改接口 | 稳定性标记 | 风险 |
|:---------|:----------|:-----|
| `authenticate()` | STABLE | 🔴 不能改签名 |
| `validatePassword()` | INTERNAL | ✅ 可以改 |

### 需要同步改的文件
1. `src/user/dto.ts` — 更新类型定义
2. `tests/auth/login.test.ts` — 更新测试
3. `.ai/L1-codebase-map/features/auth/README.md` — 更新文档

### 建议
- [是否安全 + 推荐做法]
```

### Step 2D: 规则查询

1. 读取 `.ai/L2-rules/global.md` — 全局规则
2. 如果问题涉及特定模块 → 读取 `.ai/L2-rules/<module>.md`
3. 如果问题涉及代码模板 → 读取 `.ai/L2-rules/templates.md`
4. 如果问题涉及测试 → 读取 `.ai/L2-rules/testing.md`

**输出格式**：

```
## 规则查询：[问题摘要]

### 回答
[直接引用规则文件的相关条款]

### 规则来源
- 文件：`.ai/L2-rules/global.md` L42-L55
- 原文：> [引用原文]

### 示例（如有模板）
[从 templates.md 引用代码模板]
```

### Step 2E: 需求/测试追溯

1. 读取 `.ai/L3-specs/specs/` — 按功能域找到对应的 spec
2. 如果涉及变更历史 → 扫描 `.ai/L3-specs/archive/` 下的 `proposal.md`
3. 如果涉及测试 → 读取 `.ai/L5-validation/traceability/<domain>.md`

**输出格式**：

```
## 追溯查询：[问题摘要]

### Spec 位置
- 文件：`.ai/L3-specs/specs/auth/spec.md`
- Requirement：用户登录（REQ-001）

### 实现状态（来自追溯矩阵）
| Scenario | 代码 | 测试 | 状态 |
|:---------|:-----|:-----|:-----|
| 正常登录 | `service.ts:authenticate` | `login.test.ts:45` | ✅ verified |
| 空密码 | `service.ts:validate` | — | ❌ 缺测试 |

### 变更历史（如有）
| 变更 | 时间 | 内容 |
|:-----|:-----|:-----|
| `add-password-validation` | 2024-01 | 增加了空密码校验 |
```

### Step 3: 补充源码搜索（当 .ai/ 文档不够时）

如果 Step 2 从 `.ai/` 文档中未找到足够信息：

1. 用 `grep -rn` / `find` 在源码中搜索
2. 读取找到的源码文件，提取关键信息
3. **标记为"来自源码直接搜索，非 .ai/ 文档"**，提醒用户考虑更新 `.ai/`

```
> ⚠️ 以下信息来自源码直接搜索，`.ai/` 文档中未记录。建议运行 `/update-ai` 补充。
```

### Step 4: 输出回答

组装最终回答：

1. **直接回答**（2-5 句话，先给结论）
2. **详细信息**（按 Step 2 的输出格式）
3. **相关操作建议**（如适用）：
   - 如果用户可能想修改 → 提示 `/new-change` 或 `/continue-change`
   - 如果发现 `.ai/` 文档缺失/过期 → 提示 `/update-ai`
   - 如果发现测试缺口 → 提示 `/review-tests`

## 反模式

- ❌ 不读 `.ai/` 文档就直接 grep 源码（必须先查 .ai/，不够再补搜）
- ❌ 只回答"在 src/ 目录下"（必须给到具体文件和行号级别）
- ❌ 猜测架构决策原因（必须引用 archive/ 的 proposal 或标明"无记录"）
- ❌ 影响分析只说"可能有影响"（必须列出具体文件和依赖路径）
- ❌ 回答完就结束，不提示下一步操作（每次回答都要给 actionable 建议）
