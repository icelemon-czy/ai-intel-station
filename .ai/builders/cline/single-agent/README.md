# Cline 单 Agent 模式

本文件夹包含 **单 Agent + 人工审核** 的完整构建流程。

## 与标准版的区别

| | 标准版 (`builders/cline/`) | 单 Agent 版（本文件夹） |
|---|---|---|
| 功能分析 (L1b) | subagent 并行分析 | 主 agent 逐个分析，每个暂停审核 |
| 基础设施分析 (L1b) | 主 agent 一次完成 | 主 agent 逐个，每个暂停审核 |
| 模块规则 (L2) | 主 agent + 可选 subagent | 主 agent 逐模块，每个暂停审核 |
| 任务规划 (L3) | 与标准版相同 | 与标准版相同（本身已有人工审核） |
| 适用场景 | 追求效率、功能多的项目 | 对质量要求高、需要逐项把关 |

## 文件清单

| 文件 | 说明 | 与标准版差异 |
|------|------|-------------|
| `prompt-L1a.md` | Phase 1-3 发现阶段 | 仅去除 subagent 提示 |
| `prompt-L1b.md` | Phase 4-5 深入分析 | 核心改动：无 subagent，逐项暂停 |
| `prompt-L2.md` | L2 编码规则 | Phase 5 逐模块暂停审核 |
| `prompt-L3.md` | L3 初始 Spec 构建 | 逐个能力域暂停审核 |
