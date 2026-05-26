# add-research-item

> **状态**: pending-review
> **创建**: 2026-05-10
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0  <!-- 不得 ≥ 2，防止 /fix-bug 递归 -->

## Status Machine（不要删）

```text
drafting ──→ implementing ──→ pending-review ──→ approved ──→ archived
   ↑              ↑  ↑              │
   │              │  └──────────────┘
   │              │   review 打回 (review-failed → implementing)
   │              │
   └──────────────┘
     spec 歧义回退（走 /fix-bug Step 3C）
```

| 状态 | 含义 | 由谁推进 |
| :--- | :--- | :------- |
| `drafting` | Proposal 写作中，待业务确认 | 人（业务） |
| `implementing` | Delta spec + 测试 + 代码实施中 | AI |
| `pending-review` | 绿灯完成，等 Reviewer 审查 | AI → 人 |
| `review-failed` | Review 打回，记录原因（见下方 Review Feedback） | 人 → AI |
| `approved` | Review 通过，待归档 | 人 |
| `archived` | 已归档到 `archive/` | AI（通过 /archive-change） |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
| :-- | :-- | :--------- |
| — | drafting | /new-change |
| drafting | implementing | /new-change（用户确认 proposal） |
| implementing | pending-review | /new-change Step 7 / /continue-change（全绿） |
| pending-review | review-failed | /review-tests（打回） |
| review-failed | implementing | /fix-bug（开始修） |
| pending-review | approved | /review-tests（通过） |
| approved | archived | /archive-change |

其他转移一律拒绝。不允许的转移出现时，Skill 必须报错并停止。

### 转移日志（append-only）

- `2026-05-10` — `—` → `drafting` by `/new-change` | 原因: 为统一跨渠道内容模型 ResearchItem 创建 proposal
- `2026-05-10` — `drafting` → `implementing` by `/new-change` | 原因: 用户确认三源覆盖、输出兼容、允许 partial item、去重后置、历史产物全部回填
- `2026-05-10` — `implementing` → `pending-review` by implementation | 原因: 共享模型、sidecar 接线、backfill 与新增测试已完成并通过
- `2026-05-19` — `pending-review` → `review-failed` by `/review-tests` | 原因: 测试审查发现 runtime sidecar 持久化场景缺少直接测试，部分 normalization assertion 未完整对齐 Spec THEN
- `2026-05-19` — `review-failed` → `implementing` by `/fix-bug` | 原因: 开始补齐 add-research-item 的测试覆盖缺口
- `2026-05-19` — `implementing` → `pending-review` by `/fix-bug` | 原因: 已补齐 runtime sidecar 持久化、normalization 与 backfill preservation 测试，相关回归通过

## Why

当前仓库按来源分别抓取 GitHub、arXiv 和 WeChat 内容，但还没有统一的内容抽象层。要支持跨渠道搜索、质量评分、去重和用户交互，先补一个 `ResearchItem` 统一模型是成本最低、后续复用最高的路径。

## What Changes

- 新增一个跨渠道统一内容对象 `ResearchItem`，承载标题、来源、链接、时间、作者/发布方、摘要、标签等标准字段
- 为 GitHub、papers、wechat 各自增加到 `ResearchItem` 的标准化映射
- 保持现有 CLI 抓取入口和默认 Markdown 输出能力可继续使用，避免一次性推翻现有工具
- 为未来的 search / ranking / report 能力提供统一输入结构

## Alternatives Considered

1. **继续保持各来源使用各自 `dict` / Markdown 格式，等聚合搜索时再临时统一** — 短期快，但会把标准化逻辑散落到后续每个聚合功能里，重复劳动高
2. **现在先引入统一 `ResearchItem` 抽象（当前选择）** — 先付出一次建模成本，后续 search、quality scoring、去重、交互都能复用

## Capabilities Affected

### New Capabilities

- `research-item`: 统一跨渠道内容抽象与标准化映射

### Modified Capabilities

- `github`: 在现有 repo / search 结果基础上增加标准化到 `ResearchItem` 的能力
- `papers`: 在现有论文元数据基础上增加标准化到 `ResearchItem` 的能力
- `wechat`: 在现有文章元数据基础上增加标准化到 `ResearchItem` 的能力

## Impact

影响范围将覆盖共享数据模型、至少 3 个来源工具的元数据映射，以及与之配套的测试和 `.ai` 文档。若保持现有 CLI 输出兼容，用户当前抓取命令可以不变，但内部数据流会新增一层标准化对象。

## Review Feedback

- [x] 2026-05-19 review-tests: `save_repo()` / `save_search_results()` / `save_papers()` / `fetch_article()` 的 sidecar 持久化场景缺少直接文件系统测试；现有测试主要覆盖 builder 与 historical backfill，不能证明新增抓取输出会写同目录 sidecar。Resolved by `/fix-bug`: 新增 `test_save_repo_writes_markdown_and_research_item_sidecar`、`test_save_search_results_writes_markdown_and_jsonl_sidecar`、`test_save_papers_writes_markdown_and_research_item_sidecar`、`test_fetch_article_writes_markdown_images_and_research_item_sidecar`。
- [x] 2026-05-19 review-tests: normalization 场景的 assertion 仍偏窄，未完整断言 GitHub timestamps / source-specific metadata、paper title/authors/summary/timestamps/categories、WeChat body summary metadata，以及 optional tag list 的空值降级。Resolved by `/fix-bug`: 补强 `tests/test_research_item.py` 中 GitHub / papers / WeChat normalization 与 optional metadata 断言。
- [x] 2026-05-19 review-tests: `backfill_output_tree()` 测试只断言 sidecar 被写入，未断言原有 Markdown 文件在 backfill 后仍被保留。Resolved by `/fix-bug`: backfill 测试已断言原 Markdown 内容在回填后保持不变。

## Known Gaps

- [ ] 质量评分、跨渠道去重、用户交互层不一定在本变更第一阶段全部完成，可能拆到后续变更
