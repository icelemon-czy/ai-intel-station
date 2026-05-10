# 需求变更管理流程

> 本文件是 AI 进行变更管理的完整参考。
> 部署位置：`.ai/L3-specs/change-management.md`
>
> entrypoint 文件（CLAUDE.md / .clinerules / copilot-instructions.md）引用本文件。

## L3 目录结构

```
.ai/L3-specs/
├── specs/                          ← 当前系统需求（truth）
│   ├── system.md                   ← TOR（系统级顶层需求）
│   ├── _capability-template/       ← 能力域 spec 模板
│   └── <domain>/spec.md            ← HLR（各能力域需求，可嵌套）
├── changes/                        ← 进行中的变更
│   ├── _change-template/           ← 变更模板
│   └── <name>/                     ← 每个变更一个文件夹
│       ├── proposal.md             ← 提案（为什么 + 改什么 + 决策理由）
│       ├── specs/<cap>/spec.md     ← delta spec（ADDED/MODIFIED/REMOVED）
│       └── tasks.md                ← 执行步骤（checkbox）
├── archive/                        ← 已完成变更
└── change-management.md            ← 本文件
```

## 创建变更

当收到新需求或 bug 修复请求时，按以下步骤执行：

### 1. 收集上下文

读取项目索引和已有 spec：

- `.ai/L1-codebase-map/overview.md` — 项目功能索引
- `.ai/L3-specs/specs/system.md` — 系统级需求
- `ls .ai/L3-specs/specs/` — 已有能力域
- `ls .ai/L3-specs/changes/` — 进行中的变更

根据需求定位涉及的功能和模块：

- `.ai/L1-codebase-map/features/[功能名]/README.md`
- `.ai/L2-rules/[模块名].md`
- `.ai/L3-specs/specs/[能力域]/spec.md`（如已存在）

### 2. 命名变更

用 kebab-case，如 `fix-login-special-chars`、`add-csv-export`。

### 3. 创建 proposal.md

在 `changes/<name>/proposal.md` 中填写（参考 `_change-template/proposal.md`）：

- **Why**: 为什么做、为什么是现在
- **What Changes**: 具体变更列表
- **Alternatives Considered**: 备选方案及选择理由
- **Capabilities Affected**: 新增/修改的能力域
- **Impact**: 影响范围

### 4. 生成 delta spec

为每个受影响的能力域创建 `changes/<name>/specs/<capability>/spec.md`：

**规则**：

- 新能力域 → 全部写在 `## ADDED Requirements` 下
- 修改已有能力域 → 先读 `specs/<capability>/spec.md`，完整复制要改的 Requirement 到 `## MODIFIED Requirements`，然后修改
- 删除需求 → 写在 `## REMOVED Requirements`，必须有 Reason 和 Migration
- 每个 Requirement 至少 1 个 Scenario
- Scenario 标题用 `####`（4 个 #）
- SHALL/MUST = 强制，SHOULD = 建议，MAY = 可选

### 5. 生成 tasks.md

根据 proposal + delta spec 生成执行步骤：

- 按依赖排序
- checkbox 格式：`- [ ] X.Y 描述`
- 最后一组 Verification — 从 Scenario 直接映射

### 6. 提出验收问题

主动提出 3-5 个需要人类确认的**业务**问题：

- ✅ 业务决策（"超过 10 万条时分页还是异步？"）
- ✅ 边界情况（"并发修改同一记录怎么处理？"）
- ✅ 兼容性（"旧 API 调用者需要兼容吗？"）
- ❌ 不问技术实现细节
- ❌ 不问读代码就能知道的事

**停下来等待人类回答。** 根据回答更新 delta spec 和 tasks。

### 7. 等待确认

展示完整的 proposal + spec + tasks。确认后：

1. proposal.md 状态改为 `implementing`
2. 更新 `.ai/L4-session/active-session.md` 指向该变更
3. 开始执行 tasks.md

## 归档变更

变更完成并通过确认后：

### 1. 合并 delta spec 到主 spec

对每个受影响的能力域：

- **ADDED Requirements** → 追加到主 spec 的 `## Requirements` 末尾
- **MODIFIED Requirements** → 找到同名 Requirement，整块替换
- **REMOVED Requirements** → 删除同名 Requirement 块
- **新能力域**（主 spec 不存在）→ 从 `_capability-template/` 创建新的 `specs/<cap>/spec.md`

### 2. 更新状态并移动

1. proposal.md 状态改为 `approved`
2. 移动 `changes/<name>/` → `archive/<name>/`

### 3. 确认

展示合并后的主 spec diff，让人类确认。

## 状态流转

```
changes/<name>/ (implementing)
    ↓ 代码完成 + 测试通过
changes/<name>/ (pending-review)
    ↓ 人类确认
archive/<name>/ (approved) + delta spec 合并到 specs/
```
