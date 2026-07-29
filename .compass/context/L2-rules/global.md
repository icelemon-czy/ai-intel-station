# 全局规则

> 适用于整个 research 工作区。这里的规则优先解决“真实入口、输出路径、外部依赖、文档同步”四类高频错误。

## 技术栈

- **语言 + 版本**: Python 3.10+
- **运行形态**: 本地 CLI 工作区，不是常驻服务
- **包管理器**: `uv`
- **测试**: 根级 `pytest`
- **外部依赖**: optional Camoufox（`wechat` extra）、`gh` CLI、arXiv public API

## 编码规范

### 命名约定

| 元素 | 约定 | 正确示例 | 错误示例 |
| ------ | ------ | ---------- | ---------- |
| 参考工具目录 | `kebab-case` | `tools/wechat-source/` | `tools/wechat_source/` |
| Python 文件 | `snake_case.py` | `collect_wechat.py` | `CollectWechat.py` |
| 函数 | `snake_case` | `fetch_papers_by_category()` | `fetchPapersByCategory()` |
| 变量 | `snake_case` | `output_dir` | `outputDir` |
| 常量 | `UPPER_SNAKE_CASE` | `OUTPUT_DIR` | `outputDir` |

### 语言特定规则

- 公开函数和 CLI 入口保持类型标注，尤其是写文件和网络边界函数
- 优先用 `pathlib.Path` 处理路径，不用字符串拼接路径
- 抓取、转换、落盘保持分段函数，不把所有逻辑堆进 `main()`
- 默认输出路径必须相对仓库根或参数推导，不依赖用户当前 cwd
- 所有生成文件用 UTF-8 写入
- 用户可见的进度信息可以 `print()`，但硬失败要抛异常或返回非成功状态，不要静默吞掉

### 导入规则

- 顺序：stdlib → 第三方 → 本地模块
- 业务代码按 `research/` → `collect/` / `library/` / `briefing/` / `publish/` 依赖方向组织
- 新增依赖统一更新根级 `pyproject.toml`，不要把依赖约束散到多个来源目录
- core command startup 必需的 dependency 才能放 base；source-specific heavy dependency
  放对应 optional extra，test-only dependency 放 `dev` extra
- optional source 未启用或未安装时不得阻止 `research --help`、local query、briefing、
  status 或其他独立 source 启动

## 架构规则

### 依赖方向

- ✅ `research/cli.py` → `collect/` / `library/` / `briefing/` → `output/`
- ✅ 抓取脚本 → 外部依赖 → Markdown 组装 → `output/<source>/`
- ✅ `.compass/context` 文档 → 只读引用脚本、README、SKILL、output 样例
- ❌ 历史来源目录承担真实业务入口；统一 operator surface 在 `research/cli.py`
- ❌ 一个抓取脚本直接 import 另一个抓取脚本的内部函数
- ❌ 通过手改 `output/` 来“修复”生成问题；根因必须回到生成器

### 错误处理模式

```python
# 硬失败：外部依赖不可用，直接中断当前命令
def run_gh(cmd: list[str]) -> str:
    result = subprocess.run(["gh"] + cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh failed: {result.stderr}")
    return result.stdout

# 部分失败可继续：保留上下文并继续处理剩余输入
for cat in categories:
    try:
        ...
    except Exception as exc:
        print(f"Failed to fetch {cat}: {exc}")
        continue
```

- GitHub: `gh` 失败视为硬失败
- Papers: 单类别失败允许继续其他类别，但必须打印具体类别
- WeChat live 测试: 缺少 `WECHAT_E2E_URLS` 时应跳过，不应强跑

### 数据验证规则

- WeChat URL 在任何网络请求前先走 `normalize_wechat_url()`
- GitHub repo 模式只接受 `owner/repo` 形式；不合法输入直接跳过并提示
- Papers 只接受 `AI_CATEGORIES` 白名单中的类别
- 输出路径作为参数开放时，默认仍应指向当前来源的 `output/<source>/`

## 反模式清单

- ❌ 不要先改 `output/` 样例，再倒推代码
- ❌ 不要看到历史 `main.py` 或来源目录就假设它是实际入口；先确认 `research/cli.py` 和命令文档
- ❌ 不要引入新依赖却不更新根级依赖声明
- ❌ 不要硬编码用户机器上的绝对路径
- ❌ 不要把网络依赖测试改成默认必跑
- ❌ 不要让 README / SKILL / `.compass/context` 中的命令说明和实际脚本行为脱节

## 版本控制

- **分支命名**: `feat/xxx`、`fix/xxx`、`docs/xxx`、`refactor/xxx`
- **Commit 格式**: Conventional Commits，例如 `docs(ai): map research workspace`、`fix(wechat): normalize escaped urls`
- **PR / 变更说明**: 至少写清影响模块、验证命令、是否改了 `output/` 约定

## 构建与验证命令

```bash
# 根级测试
uv run --extra dev python -m pytest tests/test_agent_first_runtime.py tests/test_research_item.py tests/test_restructure_research_architecture.py

# 统一研究入口
uv run research collect github owner/repo
uv run research collect github "query" --search
uv run research collect papers --list
uv run research collect papers cs.AI --max 10
uv sync --extra wechat
uv run research collect wechat "<wechat-url>"
uv run research query agent --source github
uv run research briefing digest agent --source github --source papers
uv run research backfill output
```

## 测试要求

- WeChat 的纯转换逻辑优先补 `pytest`，不要只做手工点跑
- GitHub / papers 目前仍缺系统化自动化测试；只要逻辑复杂度继续增长，就应该补根级 `tests/`
- 新建脚本或重要分支时，至少提供一个可复现的命令级 smoke 验证
