# 测试规范

> 当前测试面已经收敛到根级 `tests/`，并围绕统一 operator surface 组织。WeChat 仍然拥有最完整的纯函数测试；GitHub / papers 仍以 smoke run 为主，但后续优先补到根级测试而不是继续分散在来源目录。

## 测试框架

| 类型 | 框架 / 方式 | 运行命令 |
|------|-------------|---------|
| 根级单元测试 | `pytest` | `uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_wechat_collect.py` |
| WeChat live e2e | `pytest` + `e2e` marker | `WECHAT_E2E_URLS="<url1>,<url2>" uv run --with pytest python -m pytest tests/test_wechat_e2e_live.py -m e2e` |
| CLI smoke | 手动命令验证 | `uv run research collect github owner/repo` / `uv run research collect papers cs.AI --max 3` |

## 测试文件约定

- **命名**: `test_*.py`
- **位置**: 根级 `tests/`
- **测试命名模式**: `test_xxx`，必要时配合 `pytest.mark.parametrize`

## 测试结构规范

### 单元测试

- 优先覆盖纯转换函数，例如 URL 归一化、Markdown 组装、sidecar 解析与子命令 dispatch
- 只 mock 外部依赖，不 mock 同文件的纯函数拼装逻辑
- 使用 `tmp_path` 做文件落盘断言，避免污染仓库目录
- 对文本转换优先断言关键字段和链接，而不是整篇长文本逐字匹配

### Live E2E

- 只有在明确需要验证真实抓取链路时才跑
- 通过 `WECHAT_E2E_URLS` 提供 URL；未设置时应 `skip`
- live e2e 重点断言“生成了 Markdown 且包含源 URL / 图片落盘”，不要写脆弱的全文匹配

### CLI smoke

- GitHub / papers 修改后至少跑一次最小 happy path
- smoke 验证必须检查生成文件是否实际写入 `output/`，不只看终端输出
- 如果外部依赖不可用，在变更说明里明确写明阻塞点，而不是假装已验证

## 覆盖要求

- 不设全仓统一覆盖率阈值
- WeChat 的新增纯逻辑优先补 `tests/test_wechat_collect.py`
- operator surface 的参数和 dispatch 变化优先补 `tests/test_restructure_research_architecture.py`
- GitHub / papers 一旦开始有复杂分支、重试或格式转换，优先补 `tests/` 而不是长期依赖 smoke run

## 反模式

- ❌ 用真实网络请求代替本可写成纯函数测试的场景
- ❌ 不设置 `WECHAT_E2E_URLS` 却把 live e2e 失败当代码缺陷
- ❌ smoke run 只看 `print("Saved")`，不检查落盘内容
- ❌ 为了通过测试而改 `output/` 样例，而不改生成器逻辑
