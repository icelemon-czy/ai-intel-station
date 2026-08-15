# Papers 模块规则

## 公开契约

- CLI 命令：`uv run research collect papers cs.AI --max 10`
- 类别列表：`uv run research collect papers --list`
- operator 入口：`research/cli.py`
- 真实实现：`collect/papers.py`
- 默认输出：`output/papers/arXiv-<category>/`
- Daily role：new / legacy Paper 均解释为 `evidence`；不能填充 News quota，但 verified fresh
  Paper MAY 进入 dedicated arXiv lane

## 修改边界

- `AI_CATEGORIES` 是用户入口和领域边界，增删类别时同步改 `SKILL.md`、L3 spec、L5 traceability
- 文件命名逻辑在 `save_papers()`；变动会直接影响目录稳定性和历史可比性
- 子命令参数变化要同时检查 `research/cli.py` dispatch

## 风险点

- arXiv API 返回格式变化会直接影响 XML 解析
- 单类别失败当前是 warning + continue；排查时不要忽略这类部分失败
- role 与 daily selector 使用根级 fixture tests；真实 arXiv 仍只作 opt-in smoke

## 推荐验证

```bash
uv run research collect papers --list
uv run research collect papers cs.AI --max 3
uv run --extra dev python -m pytest -q tests/test_realtime_signals.py tests/test_research_item.py
```
