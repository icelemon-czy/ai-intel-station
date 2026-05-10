---
name: build-ai
description: "Build .ai project context for AI-assisted development from scratch. Use when: init .ai, setup ai context, new project setup, 构建AI上下文, 初始化.ai, build ai docs, create .ai directory, scaffold ai context, 新项目配置"
argument-hint: "Optional: target project path or specific layers (e.g., 'L1 only', 'skip L3')"
---

# Build .ai Project Context

为项目搭建完整的 `.ai/` AI 上下文目录。

> **依赖的 Builder Prompts**：本 Skill 的生成步骤依赖仓库根目录实际存在的 builder prompt 文件。运行前请确认 `builders/` 的 commit 与本 Skill 同一仓库同一版本。如果 builders 被单独更新过，可能与本 Skill 的接口不兼容。期望导航：
> - L1 builder 分为两段：`prompt-L1a.md` + `prompt-L1b.md`
> - L2 builder：`prompt-L2.md`
> - L3 builder：`prompt-L3.md`
> - L5 builder：`prompt-L5.md`
> - 查找不到时：告知用户并停止，不要自己编造 builder 逻辑。

## Five-Layer Architecture

| Layer | Purpose | Key Output |
|-------|---------|------------|
| L1 Codebase Map | Project navigation for AI | overview.md, feature docs, architecture.md, module-map, key-files |
| L2 Coding Rules | Coding standards from actual code | global.md, templates.md, module rules |
| L3 Spec-Driven Changes | Requirements specs & change management | system.md, capability specs, change-management.md |
| L4 Session State | AI working memory | active-session.md |
| L5 Validation | Spec-to-code traceability & verification | traceability matrices, validation reports |

## Prerequisites

- Target project has source code to analyze
- Know the project root path

## Procedure

Three steps. Execute in order.

---

### Step 1: Copy project-compass to `.ai/`

将 project-compass 模板复制到目标项目下：

```bash
cp -r /path/to/project-compass /path/to/your-project/.ai/
```

复制后，目录结构、模板文件、`L3-specs/change-management.md`、`L4-session/active-session.md` 等已就位；`.ai/doc-sync.md` 需要从 `.ai/entrypoints/doc-sync.md` 额外部署一次。

> 如果 `.ai/` 已存在且用户想重建，先确认是否备份。

---

### Step 2: Build L1 → L2 → L3 → L5

选择与用户 AI 工具匹配的 builder（`builders/claude/`、`builders/copilot/` 或 `builders/cline/`），**按顺序**执行 prompt。

**先读取 builder prompt 文件（不可跳过）**：读取对应目录下的所有 `prompt-*.md`（如 `builders/claude/prompt-L1a.md`），确认文件存在且内容完整。如果文件不存在或目录为空 → 告知用户并停止，不要自己编造 builder 逻辑。

每个 prompt 是独立的完整指令。复制到 AI 新对话中，填入 `[占位符]`，让 AI 执行。

| Order | Builder Prompt | What it builds | External input |
|-------|---------------|----------------|----------------|
| 1 | `prompt-L1a.md` | overview.md + feature list + `_handoff.md` | Optional: supplementary context file |
| 2 | `prompt-L1b.md` | features/ docs + architecture.md + module-map.md + key-files.md | Reads `_handoff.md` from step 1 |
| 3 | `prompt-L2.md` | global.md + templates.md + module rules | Reads L1 output |
| 4 | `prompt-L3.md` | system.md (TOR) + capability specs (HLR) | Optional: PRD / product spec / API docs |
| 5 | `prompt-L5.md` | traceability matrices + validation report | Reads L1 + L3 output |

#### Builder variants

| Tool | Directory | Subagent behavior |
|------|-----------|-------------------|
| Claude Code | `builders/claude/` | Subagent can read+write, creates files directly |
| GitHub Copilot | `builders/copilot/` | No subagents, sequential analysis, auto-continues |
| Cline (sub-agent) | `builders/cline/sub-agent/` | Subagent read-only, outputs text for main agent to write |
| Cline (single-agent) | `builders/cline/single-agent/` | No subagents, pauses for human review after each item |

#### Builder prompt details (reference)

There is no separate `references/` directory for this skill. The authoritative build logic lives in the actual builder prompt files under the selected tool directory:

- `prompt-L1a.md` — L1 Phase 1-3: scan project, identify features, write overview and `_handoff.md`
- `prompt-L1b.md` — L1 Phase 4-5: deep analysis for feature docs, architecture, module-map, key-files
- `prompt-L2.md` — extract coding rules and templates from actual code
- `prompt-L3.md` — build initial specs from code and optional external docs
- `prompt-L5.md` — build traceability, test specs, and validation output

> 读取方式：先选工具目录（如 `builders/copilot/`），再按顺序读取其中的 `prompt-L1a.md`、`prompt-L1b.md`、`prompt-L2.md`、`prompt-L3.md`、`prompt-L5.md`。不要再查找不存在的 `./references/*.md`。

---

### Step 3: Deploy entrypoint

读取对应的 entrypoint 模板文件内容，然后复制到项目根目录：

| AI Tool | Source | Target |
|---------|--------|--------|
| Claude Code | `.ai/entrypoints/claude.md` | Project root `CLAUDE.md` (if `CLAUDE.md` already exists, append content) |
| Cline | `.ai/entrypoints/clinerules.md` | Project root `.clinerules` |
| GitHub Copilot | `.ai/entrypoints/copilot-instructions.md` | Project root `.github/copilot-instructions.md` |

另外，部署 `.ai/` 内部工作流参考文件：

| Workflow Doc | Source | Target |
|--------------|--------|--------|
| Doc sync | `.ai/entrypoints/doc-sync.md` | `.ai/doc-sync.md` |

---

### Verify

All steps done. Run through this checklist. **每条必须实际执行验证命令，不允许"看了一下没问题"。**

```bash
# 1. overview.md 长度检查
wc -l .ai/L1-codebase-map/overview.md  # 必须 ≤ 60 行

# 2. feature 文档完整性
for f in .ai/L1-codebase-map/features/*/README.md; do
  grep -q "层.*表\|layer" "$f" || echo "❌ $f 缺少层导航表"
done

# 3. 关键文件存在性（每个都 test -f）
test -f .ai/L1-codebase-map/architecture.md || echo "❌ architecture.md 缺失"
test -f .ai/L2-rules/global.md || echo "❌ global.md 缺失"
test -f .ai/L2-rules/testing.md || echo "❌ testing.md 缺失"
test -f .ai/L3-specs/specs/system.md || echo "❌ system.md 缺失"
test -f .ai/L3-specs/change-management.md || echo "❌ change-management.md 缺失"
test -f .ai/doc-sync.md || echo "❌ doc-sync.md 缺失"
test -f .ai/L5-validation/validation-rules.md || echo "❌ validation-rules.md 缺失"

# 4. 至少 1 个能力域 spec
ls .ai/L3-specs/specs/*/spec.md 2>/dev/null | wc -l  # 必须 ≥ 1

# 5. 每个能力域有追溯文件
for d in .ai/L3-specs/specs/*/; do
  domain=$(basename "$d")
  [[ "$domain" == "_capability-template" ]] && continue
  test -f ".ai/L5-validation/traceability/${domain}.md" || echo "❌ 追溯文件缺失: $domain"
done

# 6. global.md 规则非空
wc -l .ai/L2-rules/global.md  # 必须 > 5 行（排除空模板）

# 7. "Can AI derive this from code?" 冗余检查
# 对 overview.md 中每个条目，检查是否仅是文件路径列表（如果是 → 删除，AI 可以 ls 获取）
```

以上检查有任何 ❌ → **修复后再宣告完成**，不允许带着缺失项交付。
