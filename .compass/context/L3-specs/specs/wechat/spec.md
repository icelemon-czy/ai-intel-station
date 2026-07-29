# WeChat Collection Specification

## Purpose

把一个 WeChat article URL 转换为本地 Markdown archive，并保留文章 metadata、图片和 ResearchItem sidecar。

## Requirements

### Requirement: Normalize Article URL

WeChat collection MUST 在 network fetch 前规范化 pasted article URL。

#### Scenario: Pasted URL contains escaped or HTML separators

- **WHEN** URL 包含 `\?`、`\&` 或 `&amp;`
- **THEN**系统将其转换为有效 `mp.weixin.qq.com` URL 后再 fetch

### Requirement: Preserve Article Content and Metadata

成功生成的 Markdown MUST 保留 title、source URL 和可获得的 publication metadata。

#### Scenario: Collect an article

- **WHEN** article fetch 和 conversion 成功
- **THEN**系统写入 `output/wechat/<article>/` 下的 Markdown
- **AND**Markdown 包含 title 与 canonical source URL

### Requirement: Localize Article Images

article body 中可下载的图片 SHOULD 保存到 article archive，并将 Markdown reference 改为 local path。

#### Scenario: Article contains supported image URLs

- **WHEN**转换后的 article body 引用了可下载图片
- **THEN**图片保存到 article 的 `images/` directory
- **AND**Markdown 引用指向 local image

### Requirement: WeChat Sidecar

成功 article collection MUST 生成可由 Library 加载的 ResearchItem sidecar。

#### Scenario: Load collected article

- **WHEN** article Markdown 写入成功
- **THEN**sidecar 包含 `source=wechat`、title、canonical URL 和 output path

### Requirement: Explicit Runtime Failure

缺失 optional WeChat runtime、缺失 browser runtime、无效 URL 或 fetch failure MUST 返回
明确失败；缺失 optional dependency 时 guidance MUST 指向 `wechat` install extra，且 CLI
MUST NOT 输出未处理的 Python traceback。

#### Scenario: Article cannot be fetched

- **WHEN** URL 无效或 browser fetch 失败
- **THEN**当前 collection 返回可读错误
- **AND**不生成伪成功 sidecar

#### Scenario: WeChat extra is not installed

- **WHEN**operator 在 core-only environment 运行 WeChat collection
- **THEN**command 返回 non-success status 与 `uv sync --extra wechat` guidance
- **AND**GitHub、Papers、query、briefing 与 discovery control action 仍可使用
