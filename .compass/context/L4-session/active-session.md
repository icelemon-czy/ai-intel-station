# 当前会话状态

> 这里只维护当前 baseline、active pointer 与下一步方向；历史 change 证据位于 L3 archive
> 和 L5 reports，不在本文件重复堆叠。

## 最后更新

- **时间**: 2026-07-30
- **主题**: Release readiness
- **状态**: 全部 local release gates 与 final SDD review 已通过；无 active L3 change，
  正在完成 Git commit / `v0.1.0` tag

## 当前 baseline

- primary interface 是 Agent + project-local Skill。
- `.agents/skills/daily-discovery/SKILL.md` 负责 Today、Preferences、Status 与明确请求的 Schedule。
- `research` CLI 是 deterministic runtime；local archive、ResearchItem sidecar、briefing 与 run log
  是 data source of truth。
- Web 保留为 optional Library / briefing viewer，不是 normal discovery 的前置条件。
- default `uv sync --frozen` 只保留 project + PyYAML；WeChat browser stack 通过
  `uv sync --extra wechat` 按需安装；pytest 通过 `dev` extra 安装。
- legacy `.ai/` 与旧 platform Workflow mirrors 已在 user review 后删除；active context
  位于 `.compass/context/`，canonical Workflow 位于 `.agents/skills/`，runtime state
  位于 `.state/discovery/`。

## 最近完成

- `add-agent-first-daily-intelligence` 已合并到 daily-discovery、
  research-operations 与 wechat main Specs，并归档。
- business Specs 当前为 10 capabilities、55 Requirements、64 Scenarios。
- Agent/discovery targeted tests 62 passed；discovery runner 14 passed；
  WeChat/sidecar regression 36 passed。
- fresh-context Today test 在 repair 后能区分 dry-run、旧 briefing 与真实 today artifact。
- full WeChat optional install 已验证：实际安装 44 packages，runtime import 成功，
  42 tests passed / 1 live e2e skipped；验证后已恢复 2-package core。
- preference write 已通过 isolated fresh-context test：只修改目标 search，保留所有未涉及
  field 和 private URL，dry-run 为 5 succeeded / 0 failed。
- final targeted regression 为 63 passed；discovery runner 14 passed；core runtime
  5 passed；test-created config/log/temp workspace 已清理。
- `align-release-validation-with-agent-first-baseline` 已通过 final review 并归档：
  core 422、runner 15、optional WeChat 16、Web 102、Vite build、artifact checker 与
  isolated Python 3.10 wheel CLI/Web smoke 全绿。
- legacy `.ai`、retired Workflow mirrors、absolute local symlinks 与 personal paths 已清理；
  merged Spec / Workflow 作为 versioned project artifacts 保留。

## 已知 gap

- 无已知 product / contract test blocker。
- WeChat live e2e 未运行，因为没有 operator-provided `WECHAT_E2E_URLS`；不冒充外部 live
  fetch evidence，也不阻断 default release。

## 下一步方向

先 dogfood Agent-first flow，观察用户真实提出 Today / Preferences / Status 时的摩擦；
收集到足够 evidence 后再重新 design Web，而不是继续扩展旧 Web-first interaction。

## Workspace

- 本轮尚未 push；正在创建本地 release commit 与 tag。
