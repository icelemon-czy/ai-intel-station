# GitHub 模块规则

## 公开契约

- CLI 命令：`uv run research collect github owner/repo`
- 搜索命令：`uv run research collect github "query" --search`
- operator 入口：`research/cli.py`
- 真实实现：`collect/github.py`
- 默认输出：`output/github/<owner-repo>/README.md` 或 `output/github/<query>/search.md`

## 修改边界

- 任何对 `gh` 调用参数的修改都属于行为变更，要同步更新 `SKILL.md` 和 `.ai`
- 子命令参数变化要同时检查 `research/cli.py` dispatch
- repo 模式输出字段改动会影响历史归档对比和下游摘要输入

## 风险点

- `gh` 未安装或未登录时，命令应明确失败
- `--issues` 参数当前和实际行为不完全一致；调整前先决定是修实现还是修文档
- 当前没有自动化测试，命令级 smoke run 是最低门槛

## 推荐验证

```bash
gh auth status
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
```