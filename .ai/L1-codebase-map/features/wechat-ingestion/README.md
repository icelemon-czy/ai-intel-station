# 微信文章抓取

## 适用任务

- 改 `mp.weixin.qq.com` 抓取逻辑
- 调整 Markdown 转换、图片本地化、元数据字段
- 排查 URL 粘贴后失败、live e2e 或 Camoufox 相关问题

## 入口与关键文件

- `research/cli.py` — 统一运行入口，负责 dispatch 到 WeChat collect 动作
- `collect/wechat.py` — 真正的抓取、转换、落盘实现
- `tests/test_wechat_collect.py` — 纯函数和转换逻辑测试
- `tests/test_wechat_e2e_live.py` — 依赖网络与真实文章 URL 的 opt-in live e2e
- `tools/wechat/README.md` / `SKILL.md` — 来源参考资料，可作为 WeChat collect 能力说明参考

## 主数据流

```text
research collect wechat <url>
  → research/cli.py dispatch
  → fetch_article(url, output_dir)
    → normalize_wechat_url()
    → AsyncCamoufox 获取文章 HTML
    → extract_metadata()
    → process_content()
    → download_all_images()
    → convert_to_markdown()
    → replace_image_urls()
    → build_markdown()
    → build_wechat_item()
    → output/wechat/<文章标题>/<文章标题>.md + research-item.json + images/
```

## 关键约束

- 默认输出根目录是仓库根下的 `output/wechat`
- 图片下载并发由 `IMAGE_CONCURRENCY = 5` 控制
- live e2e 依赖 `WECHAT_E2E_URLS`；未设置时应跳过，不应变成默认失败
- URL 归一化是已测行为，改动前先看 `tests/test_wechat_collect.py`
- 部分 code-snippet 可能是图片 / SVG，只能保留当前可解析行为
- article 目录现在包含 Markdown、images 和 normalized sidecar；改目录布局前要确认 README / backfill 一起更新

## 常见改动与联动

| 改动 | 必须一起看 |
| --- | --- |

| 调整 URL 预处理 | `normalize_wechat_url()` + `tests/test_wechat_collect.py` |
| 调整 Markdown 结构 | `build_markdown()` + README / SKILL 输出说明 |
| 调整图片处理 | `download_all_images()` + `replace_image_urls()` + live e2e |
| 调整元数据字段 | `extract_metadata()` + 生成样例 Markdown |

## 验证

```bash
uv run --with pytest python -m pytest tests/test_wechat_collect.py
uv run research collect wechat "<wechat-url>"
```

## 已知边界

- 对网络、页面结构和浏览器运行时高度敏感
- 当前自动化测试里，WeChat 仍然是转换逻辑覆盖最完整的一块，但入口已经并入统一 operator surface

