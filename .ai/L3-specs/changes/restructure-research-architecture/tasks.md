# Implementation Tasks

> Agent 根据 proposal + delta spec 生成的执行步骤。
> 用 checkbox 格式，Agent 执行时逐一勾选。

## 1. Tests

> 从 delta spec 的 Scenario 直接映射为测试用例。先写测试，确认红灯。

- [x] 1.1 为 `library` 层编写本地查询测试，覆盖跨来源查询、source filter，以及“时间可选 / 时间受限”两类场景
- [x] 1.2 为 `briefing` 层编写 Markdown 生成测试，覆盖 digest / reading list 输出和 Obsidian 友好结构
- [x] 1.3 为部分成功场景编写测试，验证缺失某个来源时仍生成简报，并明确标注缺失来源
- [x] 1.4 为兼容层编写测试，验证现有 GitHub / papers / WeChat CLI 入口在重组后仍保持当前输出行为

## 2. Structure Reshape

- [x] 2.1 新建业务化目录结构 `collect/`、`library/`、`briefing/`、`publish/`，并为其建立最小可运行模块边界
- [x] 2.2 将共享 `ResearchItem`、本地存储扫描、查询辅助逻辑迁入 `library/`，保留兼容导入路径
- [x] 2.3 为 GitHub / papers / WeChat 建立 `collect/` 层封装，让现有 `fetch_*.py` 退化为薄壳入口

## 3. Query And Reporting

- [x] 3.1 实现本地 ResearchItem 查询入口，支持关键词、标签、来源和可选时间过滤
- [x] 3.2 实现简报生成入口，至少支持 digest 与 reading list 两类 Markdown 产物
- [x] 3.3 实现部分成功提示逻辑，在缺失来源时将覆盖缺口写入简报正文或元数据区块

## 4. Output And Compatibility

- [x] 4.1 为派生简报产物建立独立输出树，保持 `output/github/`、`output/papers/`、`output/wechat/` 原始归档不变
- [x] 4.2 保持现有 CLI 命令和历史 sidecar / Markdown 可继续复用，不要求重新抓取才能查询或出简报
- [x] 4.3 更新 `.ai` 导航、能力说明和 traceability，反映新的业务层次和输出边界

## 5. Validation

- [x] 5.1 运行新增测试，确认 query / reporting / partial-success / compatibility 相关场景全部通过
- [x] 5.2 运行最小 smoke 验证，确认现有 GitHub / papers / WeChat 命令仍可到达真实入口
- [x] 5.3 运行一条本地 briefing 生成命令，确认能直接消费现有 ResearchItem sidecar 生成 Obsidian 友好的 Markdown
