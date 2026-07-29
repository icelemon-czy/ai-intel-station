# 需求变更管理

> `.compass/context/L3-specs/` 的状态与合并规则。用户只描述目标；`develop` Workflow 负责路由、验证和归档。

## Directory contract

```text
L3-specs/
├── specs/                         current confirmed behavior
├── changes/<name>/
│   ├── proposal.md                why, behavior decision, impact
│   ├── specs/<capability>/spec.md delta requirements
│   └── tasks.md                   tests first, implementation second
├── archive/<name>/                completed change evidence
└── change-management.md
```

只有可观察行为、业务规则、API、schema、权限、兼容性或迁移语义发生变化时才创建 L3 change。内部重构、机械迁移、文档和不改变契约的配置修改走 lightweight path，不创建占位 Spec。

## State machine

```text
drafting → implementing → pending-review → approved → archived
                 ↑              │
                 └ review-failed┘
```

| From | To | Condition | Owner |
|:-----|:---|:----------|:------|
| — | `drafting` | 行为变更需要 proposal/delta | Main Agent via `develop` |
| `drafting` | `implementing` | 业务歧义已解决，plan review 无阻塞项 | Main Agent |
| `implementing` | `pending-review` | 相关测试绿灯、L2 合规检查完成 | Main Agent |
| `pending-review` | `review-failed` | SDD review 返回阻塞项（技术问题或未解决的产品语义） | Main Agent |
| `review-failed` | `implementing` | 开始修复 finding 或落实已确认的产品决策 | Main Agent / `fix-bug` |
| `pending-review` | `approved` | SDD review `PASS` 且关键证据已复核 | Main Agent |
| `approved` | `archived` | delta 合并和结构验证成功 | Main Agent |

Subagent 不写状态。每次转移在 proposal 的 append-only 日志中记录证据摘要。

## Create or resume

1. 读取最小相关 L1、L2、主 Spec 和现有 changes，避免重复或冲突。
2. 用 kebab-case 命名 change。
3. 从 `_change-template/` 创建 proposal 与 tasks。
4. Delta 规则：
   - 新能力：`ADDED Requirements`
   - 修改：把原 Requirement 完整复制到 `MODIFIED Requirements` 后再改
   - 删除：`REMOVED Requirements`，记录 reason 与 migration
5. 每个 Requirement 至少一个有可观察 WHEN/THEN 的 Scenario。
6. Tasks 的第一组固定为 Scenario 测试，后续才是实现。
7. 只有答案会改变产品行为、范围、兼容性或迁移时才询问用户；问题合并成一批。
8. 恢复时交叉检查 proposal、tasks、L4、Git diff、源码和测试，以实际证据校正漂移。

## Review and repair

Main Agent 按 `.compass/context/L5-validation/validation-rules.md` 运行测试并复核证据。`sdd-reviewer` 可在 `plan` / `verify` 模式提供只读检查。

- 技术 findings 自动进入 `review-failed → implementing` 修复并重新 review。
- 业务语义冲突时保持 `review-failed` 并暂停；决策确认后进入 `implementing` 落实。
- 不能把绿灯、状态字段或 traceability 标签单独当作通过依据。

## Merge and archive

仅在状态为 `approved` 时执行：

1. ADDED 追加到主 Spec。
2. MODIFIED 按 Requirement 整块替换，禁止句子级 patch。
3. REMOVED 删除同名 Requirement。
4. 新能力域从 `_capability-template/` 创建。
5. 验证每个 Requirement 至少一个 Scenario、WHEN/THEN 完整、无孤立或重复 Requirement。
6. 更新 L5；只有实际核实的证据标为 `verified`。
7. 移动 `changes/<name>/` 到 `archive/<name>/`，清理指向它的 L4 session。

通过 review 后，合并和归档是 `develop` 的自动后置条件，不形成额外用户命令或确认。用户明确要求只实现、不归档时例外。
