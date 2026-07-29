---
name: build-context
description: "为已有代码库构建、重建或修复 Compass 项目上下文，也可单独更新测试规范。Use for brownfield onboarding or context maintenance; not for creating a new project or implementing code changes."
---

# Build Compass Project Context

在已安装项目的 `.compass/context/` 中初始化、重建或维护项目上下文。首次安装时，
平台入口、Skill 部署和 Subagent 渲染由 staging 中的 `.compass/INSTALL.md` 负责；成功
安装会删除该 staging 文件，本 Skill 的稳定运行不得依赖它。

## Non-negotiable boundaries

- 保留已有且仍有效的项目事实，增量更新，不用空模板覆盖。
- 只把源码、配置、测试、Git 历史、用户文档或用户确认过的内容写成事实。
- 无法确认的内容标记为 `[待确认：...]`；代码推断的需求不能冒充已确认需求。
- 默认由当前 Agent 完成构建。`sdd-reviewer` 服务 change 的只读 SDD 检查，不参与 context 写入。
- 不复制 Skill、不创建 Skill 软链接、不修改平台配置。

## References

按实际范围读取，不要一次性加载全部：

| Scope | Required reference |
|:------|:-------------------|
| 检查空白结构、迁移旧上下文 | [references/scaffold.md](references/scaffold.md) |
| 验证 AGENTS/平台入口边界 | [references/entrypoint.md](references/entrypoint.md) |
| 新建或重建 L1 索引、识别功能边界 | [references/l1-discovery.md](references/l1-discovery.md) |
| 深入构建 feature、architecture、module-map、key-files | [references/l1-deep-analysis.md](references/l1-deep-analysis.md) |
| 从真实代码提取 L2 规则、模板和测试规范 | [references/l2-rules.md](references/l2-rules.md) |
| 从已确认需求构建或校正 L3 Spec | [references/l3-specs.md](references/l3-specs.md) |
| 建立 L5 追溯、测试设计和验证报告 | [references/l5-validation.md](references/l5-validation.md) |

执行全量构建时，按表中顺序读取；只更新单层时，只读取该层 reference 及其明确要求的前置上下文。

## Procedure

### Step 1: Inspect before writing

1. 确认 `.compass/context/` 存在；`.compass/INSTALL.md` 只在 installation staging
   期间存在，不是已安装项目的前置条件。
2. 检查 L1-L5 当前内容，区分空模板、已确认事实和过期信息。
3. 检查是否存在旧 `.ai/`、外部需求文档或用户指定范围。
4. 报告准备构建的层；不要因为文件存在就假设内容完整。

### Step 2: Prepare context safely

新安装、结构缺失或旧 `.ai/` 迁移时，读取 `references/scaffold.md`。如果 `.compass/context/` 整体缺失，停止并要求重新复制完整 `compass/`，不要自行拼装第二套目录。

### Step 3: Build L1

先读取 `references/l1-discovery.md`，生成轻量索引、基础设施与功能清单；再读取 `references/l1-deep-analysis.md`，沿真实调用链填写功能、运行时架构、依赖关系和任务食谱。

### Step 4: Build L2

读取 `references/l2-rules.md`。从代码、lint、构建和测试配置中提取可执行规则；规则必须有证据，项目没有一致模式时保留待确认，不要发明规范。

用户只要求建立或更新测试规范时，直接走本步骤的 testing 部分：检查真实依赖、配置、CI、测试文件和可执行命令，只更新 `L2-rules/testing.md`。不要为了这一目标重建其他层，也不要求用户运行独立 setup Skill。

### Step 5: Build L3 when requirements exist

读取 `references/l3-specs.md`。优先使用用户提供或确认的需求。只有代码时可以形成待确认草案，但必须先让用户确认能力域和业务行为，再将其视为正式 Spec。

### Step 6: Use L4 only for resumable work

仅在构建被中断、需要跨会话继续时更新 `.compass/context/L4-session/active-session.md`。完成后清理临时状态，不把 L4 当永久项目文档。

### Step 7: Build L5 from checked evidence

读取 `references/l5-validation.md`。逐条检查 Spec、实现和测试；只有实际检查过实现与测试证据时才能标记 `verified`。

## Verification

至少实际检查：

```bash
test -f .compass/context/L1-codebase-map/overview.md
test -f .compass/context/L1-codebase-map/architecture.md
test -f .compass/context/L1-codebase-map/module-map.md
test -f .compass/context/L1-codebase-map/key-files.md
test -f .compass/context/L2-rules/global.md
test -f .compass/context/L2-rules/testing.md
test -f .compass/context/L3-specs/change-management.md
test -f .compass/context/L5-validation/validation-rules.md
```

然后确认：

- `overview.md` 是小型导航索引，不是源码目录转录。
- L1 的数据流、依赖和联动来自实际代码。
- L2 规则均能追溯到代码或配置。
- L3 明确区分已确认需求、文档未实现需求和代码推断草案。
- L5 没有未经检查的 `verified` 结论。
- 没有修改任何 platform Skill 或 Subagent 文件。

## Output

报告构建范围、读取的 references、已创建或更新的上下文、保留未动内容、待确认项和实际验证结果。不得只回复“上下文已构建”。
