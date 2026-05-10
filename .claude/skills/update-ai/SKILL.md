---
name: update-ai
description: "Update existing .ai project context when code changes. Use when: refresh .ai docs, code changed need to update ai context, sync .ai with code, 更新AI上下文, 刷新.ai文档, update ai docs, new feature added update docs"
argument-hint: "Optional: what changed (e.g., 'new payment feature', 'refactored auth', 'L1 only')"
---

# Update .ai Project Context

Updates an existing `.ai/` directory to reflect code changes.

## When to Use

- Code has changed significantly (new features, refactored modules)
- New files/directories added that aren't documented
- Coding patterns evolved (need to update L2 rules)
- Periodic refresh to keep docs accurate

## Prerequisites

- `.ai/` directory already exists with L1-L4 structure
- Use `/build-ai` if no `.ai/` exists yet

## Procedure

### Step 1: Assess Current State

Read the existing `.ai/` structure to understand what's documented:

```bash
# What .ai docs exist?
find .ai -name "*.md" | sort

# Current overview
cat .ai/L1-codebase-map/overview.md

# Current feature list
ls .ai/L1-codebase-map/features/

# Last session state
cat .ai/L4-session/active-session.md
```

### Step 2: Detect Changes

> **Known limitation**: `git diff --name-status` is a heuristic. It cannot reliably distinguish "new feature" from "refactor that split one file into three", or "feature removed" from "file renamed". **The detection result is a draft list, not ground truth** — Step 3 must ask the user to confirm every entry before Step 4 writes anything.

Compare current code state with documented state:

```bash
# What changed recently?
git log --oneline -30

# New/deleted/renamed files since a reference point
git diff --name-status HEAD~30 -- . ':!.ai'

# Current project structure
find . -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/build/*' -not -path '*/target/*' -not -path '*/.ai/*' | head -120 | sort

# New directories that might be new features
# Compare with features listed in overview.md
```

Identify:
- **New features**: directories/modules not in `overview.md` feature index
- **Deleted features**: documented features whose code no longer exists
- **Changed features**: significant modifications to documented features
- **New patterns**: coding patterns that differ from `global.md`
- **Infrastructure changes**: framework/config/plugin/build-system/testing changes

### Step 3: Plan Updates

Present findings to the user:

```
## 变更检测结果

### 需要新增
- [ ] 新功能: [name] — [reason]

### 需要更新
- [ ] 功能 [name] — [what changed]
- [ ] global.md — [what rules changed]

### 需要删除
- [ ] 功能 [name] — [code removed]

### 无需变更
- [features that are still accurate]
```

Wait for user confirmation before proceeding.

### Step 4: Execute Updates

Based on the plan, perform targeted updates:

#### 4a: New Features

For each new feature, run a mini L1 analysis:

1. Identify entry point and layers
2. Trace data flow
3. Create `features/[name]/README.md` + layer files
4. Add entry to `overview.md` feature index — **具体操作**：在 overview.md 的 feature 列表区段末尾追加一行 `- [name]: [一句话描述] → features/[name]/README.md`

#### 4b: Updated Features

For each changed feature:

1. Re-read the code (follow the entry points in the existing docs)
2. 对比 `git diff HEAD~N -- <feature相关文件>` 的具体变更，逐项检查：
   - 入口文件变了 → 更新 README.md 中的入口路径
   - 新增/删除了层（如新加了 middleware）→ 更新层导航表
   - 数据流变了 → 更新 data flow 描述
   - 依赖关系变了 → 更新 change impact table
3. Update layer files as needed
4. Check if module-map.md dependencies changed — **具体**：`git diff HEAD~N -- <src>` 中有新增/删除 `import`/`require` → 在 module-map.md 中 ±对应依赖箭头

#### 4c: Deleted Features

1. Remove `features/[name]/` directory
2. Remove entry from `overview.md` feature index — **具体**：删除包含该 feature name 的行
3. Update `module-map.md` (remove module, update dependency rules) — **具体**：删除以该模块为源或目标的所有依赖规则
4. Check `key-files.md` for references to deleted feature — `grep -n "<feature-name>" .ai/L1-codebase-map/key-files.md`，命中的行删除或标注"已移除"

#### 4d: L2 Rules Update

If coding patterns changed:

```bash
# Check for new patterns
grep -rn "^export\|module\.exports\|__all__" --include='*.ts' --include='*.py' --include='*.js' | head -80

# Check for new error patterns
grep -rn "extends Error\|class.*Error" --include='*.ts' --include='*.py' | head -20

# Check for new lint rules
cat .eslintrc* tsconfig.json pyproject.toml 2>/dev/null
```

对比当前代码模式和 `global.md` 中记录的模式：
- 新增的 export 模式/错误处理模式 → 追加到 global.md 对应区段
- 不再使用的旧模式 → 从 global.md 中删除或标注"已废弃"
- lint 配置变了 → 更新 global.md 中的 lint 规则引用

#### 4e: Cross-cutting Updates

After individual updates, sync:

1. **overview.md** — `ls .ai/L1-codebase-map/features/` 的目录列表 vs overview.md 中的 feature 列表，缺的补、多的删
2. **module-map.md** — 对每个模块执行 `grep -rn "import\|require" <module-dir> | grep -v node_modules`，对比已记录的依赖，有差异则更新
3. **key-files.md** — 对每个已记录的 key file 执行 `test -f <path>`，不存在的删除；`git diff --name-status` 中新增的入口文件考虑加入
4. **infrastructure/README.md** — Update if framework/config changed

### Step 5: Update Session

Update `.ai/L4-session/active-session.md`:

```markdown
- **时间**: [now]
- **对话主题**: .ai 文档更新
- **已完成**: [list of updates made]
- **下一步**: [any remaining updates or verification needed]
```

### Step 6: Verify

- [ ] `overview.md` feature index matches actual code
- [ ] No stale feature docs pointing to nonexistent code
- [ ] `module-map.md` dependency rules still accurate
- [ ] `global.md` rules match current coding patterns
- [ ] Every documented feature's entry file still exists

## Tips

- **Small updates** (1-2 features changed): Do the full procedure inline
- **Large updates** (major refactor): Consider rebuilding with `/build-ai`
- **Unsure what changed**: Use `git log --stat` to find high-impact commits
- **Regular cadence**: Run update after every significant PR merge
