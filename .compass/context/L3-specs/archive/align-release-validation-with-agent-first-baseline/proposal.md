# Align Release Validation with Agent-First Baseline

> **状态**: archived
> **创建**: 2026-07-29
> **父变更** (parent-change): 无
> **嵌套深度** (depth): 0

## Status Machine（不要删）

```text
drafting ──→ implementing ──→ pending-review ──→ approved ──→ archived
   ↑              ↑  ↑              │
   │              │  └──────────────┘
   │              │   review 打回 (review-failed → implementing)
   │              │
   └──────────────┘
     spec 歧义回退
```

| 状态 | 含义 | 由谁推进 |
|:-----|:-----|:---------|
| `drafting` | Proposal 写作中，待必要业务决策或 plan review | Main Agent / 人（仅业务歧义） |
| `implementing` | Delta spec + 测试 +代码实施中 | AI |
| `pending-review` | 绿灯完成，进入只读 SDD review | Main Agent → sdd-reviewer |
| `review-failed` | Review 有阻塞项，记录原因 | Main Agent |
| `approved` | Review PASS，进入自动归档 | Main Agent |
| `archived` | 已合并并归档到 `archive/` | Main Agent |

### 允许的状态转移（Skill 写入前必验证）

| 从 | 到 | 触发 Skill |
|:---|:---|:------------|
| — | drafting | /develop |
| drafting | implementing | /develop |
| implementing | pending-review | /develop |
| pending-review | review-failed | /develop |
| review-failed | implementing | /develop 或 /fix-bug |
| pending-review | approved | /develop |
| approved | archived | /develop |

### 转移日志（append-only）

- `2026-07-29 23:43` — [无] → [drafting] by /develop | 原因: full release gate 暴露 CI Skill root、optional dependency、fixed port 与 stale HTTP assertion 未跟随 Agent-first baseline
- `2026-07-29 23:43` — [drafting] → [implementing] by /develop | 原因: main Specs 已明确 current behavior；变更只对齐 validation wiring、fixtures 与 test oracle，无业务歧义
- `2026-07-30 00:00` — [implementing] → [pending-review] by /develop | 原因: core、optional WeChat、runner、Web、build、artifact 与 isolated wheel gates 全绿，L2/L5 evidence 已同步
- `2026-07-30 00:06` — [pending-review] → [review-failed] by /develop | 原因: review 发现 unknown/truncated Papers response 仍可能为空成功，且 CI 未安装 wheel 执行 real Web smoke
- `2026-07-30 00:06` — [review-failed] → [implementing] by /develop | 原因: behavior 与 release evidence contract 均明确，直接补 explicit failure、anti-overfit tests 与 installed-wheel CI gate
- `2026-07-30 00:10` — [implementing] → [pending-review] by /develop | 原因: blocker regression、420-test lightweight core、runner、artifact、Python 3.10 installed-wheel CLI/Web asset smoke 与 workflow lint 全绿
- `2026-07-30 00:12` — [pending-review] → [review-failed] by /develop | 原因: post-review Git audit 发现 mixed-category L3 test 联系 live arXiv 并写入 repository output
- `2026-07-30 00:12` — [review-failed] → [implementing] by /develop | 原因: test isolation contract 明确，改用 local network fixture 与 temporary output 验证真实 mixed outcome
- `2026-07-30 00:14` — [implementing] → [pending-review] by /develop | 原因: deterministic mixed-outcome test 与 full 420-test core gate 全绿，repository output/state 保持 clean
- `2026-07-30 00:18` — [pending-review] → [review-failed] by /develop | 原因: final weight audit 确认已合并的 `.ai` 与三套 retired Workflow mirrors 仍保留 1.7 MB stale context
- `2026-07-30 00:18` — [review-failed] → [implementing] by /develop | 原因: user 已授权删除；Git history 保留原文，active instruction 与 test boundary 改为 single canonical Workflow
- `2026-07-30 00:21` — [implementing] → [pending-review] by /develop | 原因: legacy context/mirrors/absolute symlinks 已删除，single-context tests 13 passed、skill lint PASS、full core 420 passed
- `2026-07-30 00:22` — [pending-review] → [review-failed] by /develop | 原因: sibling 0.4.0 audit 发现 local init-project 缺最新 Git policy，且 build-context 要求 installer 已删除的 staging file
- `2026-07-30 00:22` — [review-failed] → [implementing] by /develop | 原因: 同步 8 个 exact Workflow；对 build-context 保留最小 installed-state compatibility fix，并记录 versioned Spec policy
- `2026-07-30 00:24` — [implementing] → [pending-review] by /develop | 原因: footprint assertions 与 Agent-first runtime targeted 9 passed；8 Workflow exact match，build-context 仅有 documented compatibility diff
- `2026-07-30 00:25` — [pending-review] → [review-failed] by /develop | 原因: sensitive/path audit 发现 tracked Claude launch 与 historical report 含前开发者 absolute home path
- `2026-07-30 00:25` — [review-failed] → [implementing] by /develop | 原因: launch 改为 repo-relative runtime/output，historical evidence 只泛化 home path、不改变结论
- `2026-07-30 00:28` — [implementing] → [pending-review] by /develop | 原因: path regression 4 passed、personal path scan clean、core 422、Web 102、build/artifact/final installed-wheel smoke 全绿
- `2026-07-30 00:31` — [pending-review] → [approved] by /develop | 原因: final sdd-reviewer 核对 portability、proposal/report/session 与 supplied release gates 后返回 PASS
- `2026-07-30 00:31` — [approved] → [archived] by /develop | 原因: 无 delta Spec 待 merge；validation、single-context 与 release evidence 已进入 L2/L5，完成自动归档

## Why

release audit 在真正安装 optional runtime 并允许 loopback socket 后得到
`417 passed / 12 failed`。失败不是同一个 product regression，而是 validation surface
仍混合旧 baseline：

- GitHub Actions 强制 `.github/.claude/.Codex` 三份 legacy Skill mirror，而 canonical
  workflow 已迁到 `.agents/skills`。
- core pytest 会收集需要 `wechat` extra 的 test，无法表达 lightweight default boundary。
- HTTP tests 使用固定 port，多个 module 顺序运行时互相碰撞。
- 部分 HTTP assertion 仍绑定旧 response shape、旧 key 或 capitalization，与 main Spec
  和当前 frontend consumer 不一致。

## What Changes

- CI 以 `.agents/skills` 为 canonical workflow root，并分开 core、optional WeChat、Web gates。
- broad Python gate 明确排除 pytest-incompatible runner module，并单独用 unittest 执行。
- HTTP subprocess tests 使用 kernel-assigned free port，并等待真实 readiness。
- stale assertions 改为 user-visible contract：navigation section ids、briefing content、
  metadata purpose blocks、structured collect error。
- 清理 Python 3.12 `utcnow()` warning，同时保持 `Z`-suffixed UTC output contract。
- 删除已完成 user review 的 legacy `.ai` snapshot 与 retired platform Workflow mirrors；
  只保留 `.agents/skills` canonical tree、`.codex/agents/sdd-reviewer.toml` 与
  daily-discovery thin adapters。
- 同步 sibling Project Compass 0.4.0 的 `init-project` 更新；修复 installed
  `build-context` 依赖已被 installer cleanup 删除的 `INSTALL.md` 的 upstream contradiction。
- 本项目将 merged Spec / Workflow 作为 versioned release artifacts，不采用会使 release
  缺失 replacement truth 的 generic local-only exclude。

## Alternatives Considered

1. **把 implementation 改回旧 test shape** — 会破坏当前 frontend consumer 与 main Spec。
2. **继续维护固定 test 清单** — 新 test 文件容易再次漏出 CI。
3. **全套 optional runtime 装进 core gate** — 让 lightweight default boundary 失真。
4. **分层 release gates + broad discovery（当前选择）** — core、WeChat、Web 各自有明确
   dependency boundary，同时完整覆盖所有 test module。

## Capabilities Affected

### New Capabilities

- 无。

### Modified Capabilities

- 无 behavior Spec 变更；对齐 system validation、Web Workspace、Collection 与 Briefing
  已有 contract evidence。

## Impact

- CI: `.github/workflows/validate.yml`
- Tests: `tests/test_e2e_http.py`、`tests/test_l3_http_e2e.py`、
  `tests/test_service_e2e.py`、`tests/test_web_workspace.py`
- Runtime warning cleanup: `workspace_web/service.py`
- Documentation: L2 testing、L5 release report
- Context cleanup: `.ai/`、legacy `.Codex/.codex` Skills、retired `.github/.claude` mirrors

## Review Feedback

- `2026-07-30` BLOCKED：Papers unknown category 与 oversized/truncated response 在
  `raise_on_error=True` 时仍返回 empty success；补统一 `PapersFetchError` 与 header /
  full-buffer anti-overfit tests。
- `2026-07-30` BLOCKED：artifact checker 未核对 `index.html` 实际引用，CI 也未安装 wheel
  运行 CLI / real HTTP smoke；补 referenced asset validation 与 isolated installed-wheel gate。
- `2026-07-30` post-review audit：`test_invalid_category_reported_and_does_not_block_valid_one`
  联系 live arXiv，且未传 temporary output；即使 test 绿色也会污染 worktree。改用 local Atom
  fixture，要求 valid category 实际写入 temp archive，unknown category 仍显式报告。
- `2026-07-30` weight audit：`.ai` merge 已完成且 user 已授权删除，但 repository 仍保留
  240-file snapshot 与 40+ copied legacy Skills。删除后由 Git history 提供审计回溯，
  active tests 强制只有 `.compass/context` + `.agents/skills` 一套 source of truth。
- `2026-07-30` sibling 0.4.0 audit：installed `init-project` 落后 source 的 local Git policy；
  `build-context` source 同时要求 cleanup 后不存在的 `INSTALL.md`。前者 exact sync，后者
  使用 3-hunk installed-state fix，并用 footprint regression 固化。
- `2026-07-30` portable config audit：tracked Claude launch 与 historical report 包含
  前开发者 absolute home path。launch 改为 repo-relative runtime/output，report 只把
  cache path 泛化为 `$HOME`；全仓 personal path / credential scan clean。

## Known Gaps

- WeChat live e2e 仍需 user-provided `WECHAT_E2E_URLS`，不属于 default release gate。
