# Compass Context

本目录在复制后成为目标项目的 `.compass/context/`。

这里 **不是** 项目知识。项目知识在仓库自己的 README 和 `doc/`。

| 文件 | 谁写 | 用途 |
|:-----|:-----|:-----|
| `cli-worker.md` | 安装器 | planner 是否可以调用 Claude Code CLI 及 bounded execution config |
| `README.md` | 本文件 | 说明这个目录不是项目知识 |

Planner 在每次 implementation delegation 前覆盖 `cli-worker-task.md`，写入一个完整且 bounded 的 task spec。Runtime 可以生成 `cli-worker.lock`、`cli-worker-state.json` 与 `cli-worker-audit.jsonl`；相同 task content 成功后再次调用只返回已有结果，不再次启动 Claude。Audit 与 state 不保存 task 内容、tool input、prompt、CLI output 或 secret。

普通产品工作不得改 `cli-worker.md` 的 `status`。
