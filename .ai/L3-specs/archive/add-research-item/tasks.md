# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 为共享 `ResearchItem` 模型编写标准化与 JSON 序列化测试，覆盖 GitHub repo / search、paper、wechat article 三类输入
- [x] 1.2 为历史回填编写解析测试，覆盖现有 `output/github`、`output/papers`、`output/wechat` 样本
- [x] 1.3 为 GitHub / papers / wechat 新输出编写 sidecar 写入测试，并验证现有 Markdown 路径保持不变

## 2. Shared Model

- [x] 2.1 新增共享 `ResearchItem` 模型、序列化函数和 sidecar 写入辅助函数
- [x] 2.2 新增从 GitHub、paper、wechat 元数据构建 `ResearchItem` 的适配器
- [x] 2.3 新增从历史 Markdown / 搜索结果回填 `ResearchItem` 的解析器

## 3. Source Integration

- [x] 3.1 将 GitHub repo / search 输出接入 `ResearchItem` sidecar 生成
- [x] 3.2 将 papers 输出接入每篇论文的 `ResearchItem` sidecar 生成
- [x] 3.3 将 wechat 输出接入 article 级 `ResearchItem` sidecar 生成

## 4. Backfill And Validation

- [x] 4.1 新增历史产物 backfill 命令或脚本，覆盖现有 `output/github`、`output/papers`、`output/wechat`
- [x] 4.2 更新相关 README / `.ai` 文档与 traceability，确保新能力有导航和验证锚点
- [x] 4.3 运行新增测试与最小 smoke 验证，确认现有 CLI 输出兼容
