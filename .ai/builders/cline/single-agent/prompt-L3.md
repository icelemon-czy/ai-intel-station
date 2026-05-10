# Cline 构建 L3 初始 Spec — Prompt 模板（单 Agent 模式）

> 将以下 prompt 复制到 Cline 对话中使用。
> 使用前替换 `[项目目录]` 为实际值。
>
> **前置条件**: 已用 `prompt-L1a.md`/`prompt-L1b.md` 和 `prompt-L2.md` 完成 L1/L2 文档生成。
> **本文件范围**: 构建初始需求规格（system.md + 各能力域 spec）。支持两种输入：
> - 有需求文档（PRD / 产品规格 / 原型说明）→ 从文档提取 + 代码验证
> - 无需求文档 → 从代码逆向生成
> **核心差异**: 逐个能力域生成 spec，每个暂停等待人工审核后再继续。

---

## Prompt：构建 L3 初始 Spec

````markdown
# 为项目构建初始需求规格

## 背景

我的项目已有代码和 L1/L2 文档，但 L3-specs 还是空模板。需要构建初始需求规格。

## 目标

[填写范围，如“全部”、“只做用户认证和数据导出”、“先做 system.md”]

## 已有需求文档（可选）

[如果有 PRD、产品规格、原型说明、API 文档等，在这里提供文件路径或粘贴内容：]

- [文件路径或内容]

## 你的工作步骤

### Step 1: 读取全局上下文

```bash
# 项目总览
cat [项目目录]/.ai/L1-codebase-map/overview.md

# 运行时架构
cat [项目目录]/.ai/L1-codebase-map/architecture.md

# 功能列表
ls [项目目录]/.ai/L1-codebase-map/features/

# 全局编码规则（可能包含跨域约束）
cat [项目目录]/.ai/L2-rules/global.md

# 当前 spec 状态
cat [项目目录]/.ai/L3-specs/specs/system.md
ls [项目目录]/.ai/L3-specs/specs/

# 读取模板
cat [项目目录]/.ai/L3-specs/specs/_capability-template/spec.md
```

如果用户提供了需求文档，先读取并摘要：

```bash
# 读取用户提供的需求文档
cat [文档路径]
```

> **有需求文档时**：文档是主要输入，代码用于验证和补充细节。
> **无需求文档时**：代码 + L1 文档是唯一输入，需要推断。

### Step 2: 生成 system.md（TOR）

如果 `system.md` 还是空模板，先填充它：

**有需求文档时** — 从文档中提取：
- System Boundary — 文档中对系统范围的描述
- Cross-Cutting Requirements — 文档中明确写的跨域约束（如性能指标、安全要求）
- 用代码验证：文档写的约束在代码中是否已实现，标注差异

**无需求文档时** — 从代码推断：
- System Boundary — 系统是什么、不是什么、边界在哪
- 核心技术约束（如运行环境、依赖的外部系统）

**从跨 feature 共性模式提取 Cross-Cutting Requirements**：
- 认证/授权（如果多个功能共享同一套认证机制）
- 错误处理标准（如果 global.md 或代码中有统一的错误格式）
- 性能要求（如果有 SLA 或监控配置）
- 日志/审计（如果有统一的日志基础设施）

> 跨域约束才放 system.md，特定功能的约束放各自的 spec。

**⏸️ 展示 system.md 内容，等待人工审核后再继续。**

### Step 3: 识别能力域

**有需求文档时** — 从文档的功能模块/章节结构出发，结合 L1 features/ 交叉验证。
**无需求文档时** — 从 L1 的 features/ 列表出发。

两种情况都需要**映射**为能力域列表：

⚠️ Feature ≠ 能力域。映射规则：

| 情况 | 处理 | 示例 |
|------|------|------|
| 多个 feature 属于同一业务域 | 合并为一个能力域 | login + register + password-reset → `user-auth` |
| 一个 feature 包含多个独立职责 | 拆分为多个能力域 | user-management (含 CRUD + 权限) → `user-profile` + `user-permissions` |
| 纯技术性 feature | 考虑放入 system.md 的 cross-cutting | logging, monitoring → system.md |
| feature 是另一个的子集 | 用子能力域表达 | payment → `payment/spec.md` + `payment/refund/spec.md` |

**输出**：能力域列表 + 与 feature 的映射关系。

**⏸️ 展示能力域列表，等待人工确认后再继续。**

### Step 4: 逐能力域生成 HLR

**⚠️ 一次只处理一个能力域**。对当前能力域：

1. **读取相关 feature 文档**：
   ```bash
   cat [项目目录]/.ai/L1-codebase-map/features/[功能名]/README.md
   # 按需深入各层文件
   ```

2. **读取关键源码** — 根据 L1 指引，定位核心逻辑文件

3. **如果有需求文档** — 读取文档中对应该能力域的章节，提取需求，用代码验证实现状态

4. **生成 `specs/<domain>/spec.md`**：
   - Purpose — 一句话描述职责
   - Requirements — 每个独立的行为写一个 `### Requirement:`
   - Scenarios — 每个 Requirement 至少 1 个 `#### Scenario:`，用 WHEN/THEN 格式

4. **判断层级深度**：
   - 一个能力域有 > 5 个互不相关的 Requirement → 考虑拆分子能力域
   - 拆分后每个子能力域 2-5 个 Requirement 为最佳

5. **标注来源置信度**：
   - 来自需求文档 + 代码已实现 → 高置信度，无需标注
   - 来自需求文档但代码未实现 → 标注 `<!-- ℹ️ 文档要求，代码未实现 -->`
   - 仅从代码推断 → 标注 `<!-- ⚠️ 从代码推断，待确认 -->`

**⏸️ 展示当前能力域的 spec，等待人工审核。确认后处理下一个能力域。**

### Step 5: 质量检查

全部能力域生成完毕后，自查：

- [ ] 每个 Requirement 至少有 1 个 Scenario
- [ ] Scenario 标题用 `####`（4 个 #），不是 `###`
- [ ] SHALL/MUST = 强制，SHOULD = 建议，MAY = 可选 — 使用正确
- [ ] 不包含实现细节（"用 Redis 缓存"是实现，"SHALL cache results"是需求）
- [ ] 从代码推断的不确定点已标记 `<!-- ⚠️ 从代码推断，待确认 -->`
- [ ] 文档要求但代码未实现的已标记 `<!-- ℹ️ 文档要求，代码未实现 -->`

### Step 6: 最终确认

展示所有 spec 的完整内容。**等待确认后写入文件。**

## 输出

完成后应有：
1. ✅ `specs/system.md` — 系统级顶层需求（TOR）
2. ✅ `specs/<domain>/spec.md` — 每个能力域的需求（HLR）
3. ✅ 如有子能力域 → `specs/<domain>/<sub>/spec.md`
4. ⏸️ 等待我确认不确定点
````

---

## 使用流程总结

```
1. 确保 L1/L2 已构建完成
2. 复制上方 Prompt，填入 [项目目录] 和范围
3. 如有需求文档，填入「已有需求文档」章节
4. Agent 生成 system.md → ⏸️ 你审核
5. Agent 列出能力域 → ⏸️ 你确认
6. Agent 逐个生成 spec → ⏸️ 每个你审核
7. 你补充业务规则 → Agent 更新 → 完成
```
