# .ai 文档同步流程

> 本文件是 AI 在 git commit 前同步 .ai 文档的参考。
> 部署位置：`.ai/doc-sync.md`
>
> `git-commit` skill 在提交前引用本文件。

## 适用范围

仅覆盖 **L1（Codebase Map）** 和 **L2（Coding Rules）** 的同步。
L3 spec 的更新由 `change-management.md` 的归档流程处理。

## 何时触发

**在 git commit 前**，检查本次待提交的变更是否命中以下任一操作：

| 代码变更类型 | 需要更新的文档 |
|-------------|---------------|
| 新增功能模块 | overview.md 功能索引 + 新建 `features/[name]/README.md` + module-map.md |
| 删除功能模块 | overview.md 功能索引 + 删除 `features/[name]/` + module-map.md |
| 重命名 / 重组模块 | overview.md + 相关 feature README + module-map.md |
| 新增 / 修改入口文件 | key-files.md 任务食谱 |
| 架构变更（新中间件、启动顺序等）| architecture.md |
| 基础设施变更（框架、构建、测试等）| `infrastructure/README.md` |
| 引入新编码模式 / 规范 | global.md + templates.md |
| 模块级规则变化 | `L2-rules/[模块名].md` |

**不需要触发**：纯业务逻辑修改（不改结构）、bug 修复（不引入新模式）、配置值调整。

## 同步步骤

### 1. 快速检查

对照上表，判断本次改动是否命中任何行。没有命中 → 跳过，不需要同步。

### 2. 更新 L1 文档

按影响范围操作：

**新增功能**：
1. 在 `overview.md` 功能索引表中添加条目
2. 创建 `features/[name]/README.md`（参考同目录其他功能的格式）
3. 在 `module-map.md` 中添加依赖关系

**删除功能**：
1. 从 `overview.md` 功能索引表中移除条目
2. 删除 `features/[name]/` 目录
3. 从 `module-map.md` 中移除相关依赖
4. 检查 `key-files.md` 是否有引用

**修改功能结构**：
1. 重新阅读代码，更新 `features/[name]/README.md` 的数据流和层级
2. 检查 `module-map.md` 的依赖关系是否仍准确

**架构 / 基础设施变更**：
1. 更新 `architecture.md` 或 `infrastructure/README.md` 的相关部分

### 3. 更新 L2 文档

**新编码模式**：
1. 在 `global.md` 中添加规则或更新反模式清单
2. 在 `templates.md` 中添加新的代码模板

**模块规则变化**：
1. 更新 `L2-rules/[模块名].md` 的编码约束和合约

### 4. 验证

- overview.md 功能索引与实际代码一致
- 没有指向不存在代码的 feature 文档
- module-map.md 的依赖关系仍然准确
- global.md 的规则反映当前编码实践
