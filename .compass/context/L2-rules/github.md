# GitHub 模块规则

## 公开契约

- CLI 命令：`uv run research collect github owner/repo`
- 搜索命令：`uv run research collect github "query" --search`
- operator 入口：`research/cli.py`
- 真实实现：`collect/github.py`
- 默认输出：`output/github/<owner-repo>/README.md` 或 `output/github/<query>/search.md`
- Daily role：new / legacy GitHub repository 与 search item 均解释为 `evidence`；不能填充
  News quota，但 verified fresh item MAY 进入 dedicated GitHub lane

## 修改边界

- 任何对 `gh` 调用参数的修改都属于行为变更，要同步更新 `SKILL.md` 和 `.compass/context`
- 子命令参数变化要同时检查 `research/cli.py` dispatch
- repo 模式输出字段改动会影响历史归档对比和下游摘要输入
- search 必须按 recent update 请求并保存 available created/updated metadata；不得把 lifetime stars 排序称为今日 trend
- search success 必须返回真实 Markdown `Path`，run report 不得序列化空路径

## 风险点

- `gh` 未安装或未登录时，命令应明确失败
- `--issues` 参数当前和实际行为不完全一致；调整前先决定是修实现还是修文档
- search metadata/order/path 与 evidence role 由根级 tests 保护；live `gh` smoke 仍用于外部认证链路

## 推荐验证

```bash
gh auth status
uv run research collect github owner/repo
uv run research collect github "agent harness" --search
uv run --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_research_item.py
```
