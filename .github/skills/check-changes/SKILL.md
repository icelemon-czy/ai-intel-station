---
name: check-changes
description: "Check status of all in-progress and recent changes. Use when: 变更状态, 进度, change status, what's in progress, 当前变更, 查看变更, show changes, list changes, 有哪些变更"
argument-hint: "Optional: specific change name or 'all' for full history including archive"
---

# Check Changes Status

汇总 `.ai/L3-specs/` 下所有变更的状态，给出全局视图。

## Prerequisites

- `.ai/L3-specs/` 目录已存在
- 至少有 `changes/` 或 `archive/` 目录

## Procedure

### Step 1: 扫描进行中的变更

```bash
# 列出所有进行中的变更
ls .ai/L3-specs/changes/ | grep -v _change-template

# 如果用户要看全量（含归档）
ls .ai/L3-specs/archive/ 2>/dev/null
```

### Step 2: 读取每个变更的状态

对 `changes/` 下的**每个变更文件夹**：

1. 读取 `proposal.md` — 提取状态（drafting / implementing / review-failed / pending-review / approved）、Why、What Changes
2. 读取 `tasks.md` — 统计 checkbox 完成率：`已完成 / 总数`
3. 检查 `specs/` — 列出受影响的能力域

### Step 3: 输出汇总

用以下格式展示：

```
## 变更状态总览

### 草稿中 (N)
[状态为 drafting 的变更]

### 进行中 (N)

#### 1. <change-name>
- **状态**: implementing
- **目的**: [proposal.md 中的 Why，一句话]
- **进度**: tasks 5/12 完成
- **受影响能力域**: [列表]
- **下一步**: [tasks.md 中下一个未完成的 checkbox]

#### 2. <change-name>
...

### 打回待修复 (N)
[状态为 review-failed 的变更]

### 待审核 (N)
[状态为 pending-review 的变更]

### 待归档 (N)
[状态为 approved 的变更]

### 最近归档 (N)
[archive/ 下最近 5 个，显示名称 + 状态 + 归档时间]
```

### Step 4: 发现问题

检查是否有异常情况，主动告知用户：

- ⚠️ 变更的 tasks.md 中有超过 **7 天**未推进的 checkbox（依据：`git log --format='%ai' -1 -- .ai/L3-specs/changes/<name>/`，如最后修改距今 > 7 天则告警）
- ⚠️ active-session.md 指向的变更与 changes/ 中的不一致
- ⚠️ 有变更缺少 delta spec（proposal 有但 specs/ 为空）
- ⚠️ 有变更缺少 tasks.md

> 如果 `changes/` 为空，告知用户"没有进行中的变更"并建议使用 `/new-change` 创建。
