# Papers 模块规则

## 公开契约

- CLI 命令：`uv run research collect papers cs.AI --max 10`
- 类别列表：`uv run research collect papers --list`
- operator 入口：`research/cli.py`
- 真实实现：`collect/papers.py`
- 默认输出：`output/papers/arXiv-<category>/`

## 修改边界

- `AI_CATEGORIES` 是用户入口和领域边界，增删类别时同步改 `SKILL.md`、L3 spec、L5 traceability
- 文件命名逻辑在 `save_papers()`；变动会直接影响目录稳定性和历史可比性
- 子命令参数变化要同时检查 `research/cli.py` dispatch

## 风险点

- arXiv API 返回格式变化会直接影响 XML 解析
- 单类别失败当前是 warning + continue；排查时不要忽略这类部分失败
- 当前没有自动化测试，最少做一次 `--list` 和一次实际抓取 smoke run

## 推荐验证

```bash
uv run research collect papers --list
uv run research collect papers cs.AI --max 3
```