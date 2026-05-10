---
name: git-commit
description: "Stage, commit, and push changes with an auto-generated conventional commit message. Use when: ready to commit, git push, summarize changes, commit message."
argument-hint: "optional branch or extra context"
tools: [run_in_terminal]
---

## Step 1 — Summarize Changes

Run `git status --short` and `git diff HEAD`. If nothing changed, report "nothing to commit" and stop.

Summarize what changed and why into a **conventional commit message**:
- Subject: `<type>(<scope>): <summary>` (imperative mood, ≤72 chars)
- Body: bullet points grouped by change area

Do NOT ask the user to write the message.

## Step 1.5 — Check README

Before committing, check whether `README.md` (and `README.zh.md` if it exists) were updated:

```bash
git diff HEAD --name-only
```

- If **any non-README files** are staged/changed AND **neither `README.md` nor `README.zh.md`** appears in the changed files, warn the user:

  > ⚠️ **README not updated.** The following files changed but README.md was not updated:
  > `<list of changed files>`
  >
  > Please update README.md (and README.zh.md if applicable) to reflect these changes, or confirm that no README update is needed.

- Ask the user: "Do you want to proceed without updating the README, or should I update it first?"
- If the user confirms to proceed without README changes, continue to Step 2.
- If the user wants README updated, stop and offer to update it.

Skip this check if the only changed files are `README.md`, `README.zh.md`, or files inside `.ai/L4-session/` (session state updates don't require README changes).

## Step 2 — Doc Sync Check

在提交前，检查待提交的代码变更是否需要同步 `.ai/` 文档：

1. 读取 `.ai/doc-sync.md`（如存在）；**如果文件不存在 → 跳过本步骤**
2. 对照变更列表，按以下规则逐条判断是否命中同步条件：

| 变更类型 | 命中条件 | 需同步的文档 |
|:---------|:---------|:-------------|
| 新增/删除/重命名 src 文件 | `git diff --name-status` 中出现 A/D/R 且路径在 src 目录 | L1: overview.md, key-files.md, module-map.md |
| 新增/修改 export/public API | `git diff` 中有新增 `export`、`pub fn`、`def` 等入口 | L1: features/ 对应 README.md |
| 修改 lint/tsconfig/build 配置 | 变更列表含 `.eslintrc*`、`tsconfig*`、`pyproject.toml` 等 | L2: global.md |
| 修改测试配置或约定 | 变更列表含 `jest.config*`、`vitest.config*`、`conftest.py` 等 | L2: testing.md |
| 其他（仅业务逻辑变更） | 不命中以上任何一条 | 无需同步 |

3. 如果命中 → 按 doc-sync.md 的步骤更新对应文档，将更新一并纳入本次提交
4. 如果没命中 → 跳过

## Step 3 — Commit & Push

Using the summary from Step 1:
1. `git add -A`
2. `git commit -m "<subject>" -m "<body>"`
3. Set proxy before pushing: `export http_proxy="http://127.0.0.1:10080" https_proxy="http://127.0.0.1:10080"`
4. Push to current branch (`--set-upstream` if new branch)

Report the commit hash and branch name after pushing.
