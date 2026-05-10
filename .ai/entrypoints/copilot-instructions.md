# AI 导航指令（GitHub Copilot 版）

> 复制本文件到项目的 `.github/copilot-instructions.md`

你有一套项目文档在 `.ai/` 下，按以下流程工作：
## Skill 触发规则（重要）

项目 `.github/skills/<name>/SKILL.md` 提供了工作流 playbook。Copilot 本身没有原生 skill 发现，故按以下规则手动触发：

1. 当用户输入以下斐命令（识别为明确意图） → 打开并**完整遵循**对应 SKILL.md 的 Procedure：
   - `/git-init`、`/git-commit`
   - `/init-project`、`/build-ai`、`/update-ai`、`/setup-testing`
   - `/new-change`、`/continue-change`、`/check-changes`
   - `/review-tests`、`/fix-bug`、`/archive-change`、`/ask-codebase`
2. 当用户未输入斐命令，但描述命中某 SKILL.md `description:` 里的关键词（中英任一）→ 先提示用户：“这看起来是 `/xxx` 的场景，需要按该流程走吗？”，确认后再执行。
3. 多个斐命令只能串行，不得并行触发。
4. SKILL 中的 “等待用户确认” 步骤必须停下来等，不得自行后续。
## 每次对话启动时（自动）

读取以下 3 个文件，建立基础认知：

1. `.ai/L1-codebase-map/overview.md` — 项目功能索引（< 60 行）
2. `.ai/L2-rules/global.md` — 全局编码规则与反模式
3. `.ai/L4-session/active-session.md` — 上次进度与下一步动作

## 收到请求后

1. **查索引** — 在 overview.md 的功能索引表中匹配请求涉及的功能
2. **读功能文档** — 读取 `.ai/L1-codebase-map/features/[功能名]/README.md`
   - 按需深入：各层 `.md` 文件（文件名反映实际架构层，如 handler.md / service.md / repo.md）
3. **读模块规则** — 读取 `.ai/L2-rules/[模块名].md`（编码约束 + 合约）
4. **做通用操作时** — 查 `.ai/L1-codebase-map/key-files.md`（任务食谱）
5. **跨模块修改时** — 查 `.ai/L1-codebase-map/module-map.md`（变更联动表）
6. **理解运行时结构时** — 查 `.ai/L1-codebase-map/architecture.md`（请求生命周期 + 启动顺序 + 运行时协作）
7. **改底层基础设施时** — 查 `.ai/L1-codebase-map/infrastructure/README.md`（框架基类、配置、插件、构建流程、测试基础设施等）
8. **创建新文件时** — 查 `.ai/L2-rules/templates.md`（标准代码模板）
9. **查当前需求** — 读取 `.ai/L3-specs/specs/system.md`（TOR）和相关 `specs/<domain>/spec.md`（HLR），了解当前需求定义
10. **判断变更路径**：
    - 已有 spec 范围内的修复 / 实现 → 直接实现
    - 新增或修改系统行为 → 创建变更：
      1. 在 `changes/<name>/` 创建 proposal.md（参考 `_change-template/`）
      2. 展示 proposal + 业务问题给用户确认
      3. 确认后自动执行：delta spec → 写测试（红）→ 实现代码（绿）→ 完成
    - 参考历史变更 → 读取 `.ai/L3-specs/archive/` 目录

## 对话结束时

更新 `.ai/L4-session/active-session.md`：
- 当前做到哪一步
- 涉及文件的状态
- 测试运行结果
- 下一步具体动作

同步变更状态：
- 执行中 → proposal.md 状态为 `implementing`
- 代码完成 + 测试通过 → proposal.md 状态改为 `pending-review`，等待 `/review-tests`
- `/review-tests` 打回 → proposal.md 状态改为 `review-failed`，记录 Review Feedback
- `/review-tests` 通过（含非阻塞 Known Gaps）→ proposal.md 状态改为 `approved`
- `/archive-change` 完成 → proposal.md 状态改为 `archived`，并移动变更到 `archive/`

L1/L2 文档同步由 git commit 流程处理，对话中不需要手动同步。

## 关键约束

- 开始实现前先查 `.ai/L3-specs/changes/`，确认无冲突的进行中变更
- 修改代码前先查 overview.md 定位功能，不要盲目 grep
- 注意 overview.md 的「雷区清单」，不要碰标记的文件/配置
- 遵守 global.md 的所有规则，特别是「反模式清单」
- 跨模块修改前先查 module-map.md 的「变更联动表」
- 做了重要架构决策 → 记录到 proposal.md 的 Alternatives Considered 中
