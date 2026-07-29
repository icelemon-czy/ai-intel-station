# Implementation Tasks

## 1. Tests

- [x] 1.1 Agent Skill contract 覆盖 Today、first-run preference、read-only status、explicit schedule 与 negative trigger
- [x] 1.2 Fresh base dependency 不包含 WeChat/browser/test stack；即使 dev environment 已安装 optional packages，core dry-run 也不得 import 它们
- [x] 1.3 Missing WeChat extra 返回 non-success 与明确 install guidance，不泄漏 traceback
- [x] 1.4 Existing WeChat runtime behavior 与 source-isolated discovery tests 保持通过

## 2. Agent-first Skill

- [x] 2.1 将 existing daily-discovery Skill 从 CLI tutorial 改成 Agent-operated Workflow
- [x] 2.2 同步 AGENTS routing，明确 Web 是 optional viewer

## 3. Lightweight Runtime

- [x] 3.1 将 WeChat stack 与 pytest 从 project base dependency 拆成 optional extras
- [x] 3.2 为 missing WeChat runtime 增加 typed error 与 CLI guidance
- [x] 3.3 更新 lockfile 与 install documentation

## 4. Validation and Context

- [x] 4.1 运行 core bootstrap、CLI、discovery 与 WeChat relevant tests
- [x] 4.2 同步 L1/L2 与 L5 traceability
- [x] 4.3 完成 SDD verify、合并 main Specs 并 archive change
