# L5 验证规则参考

> 这个仓库的验证分成两层：一层验证 `.ai` 文档是否映射到真实代码，另一层验证各抓取能力的 spec 是否被代码和测试覆盖。

## 验证范围

当前默认验证 4 个主域：

- `system`
- `wechat`
- `github`
- `papers`

额外的 operator surface、query、reporting、archive-output 行为，优先通过 change delta spec 和根级测试追踪。

## 1. 结构验证（Spec 格式）

检查 L3 spec 是否符合格式规范：

- [ ] 每个 `### Requirement:` 至少有 1 个 `#### Scenario:`
- [ ] Scenario 使用 `- **WHEN** / - **THEN**` 格式
- [ ] `system.md` 同时包含 System Boundary 和 Cross-Cutting Requirements
- [ ] Requirement 语句描述行为，不直接写实现细节

## 2. 正向追溯（Spec → Code → Test）

对每个 domain：

1. 从 L3 spec 读取 Requirement / Scenario
2. 从 L1 feature 文档定位代码入口和关键函数
3. 检查 THEN 是否能在代码里找到对应行为
4. 记录已有测试或命令级验证证据
5. 标注为 `verified`、`partial`、`untested` 或 `missing`

**证据优先级**：

1. 自动化测试
2. 明确的纯函数实现 + 单元验证
3. 手工 smoke 命令
4. 仅代码存在、无验证证据

## 3. 反向追溯（Code → Spec）

优先检查这些代码路径是否有 spec 覆盖：

- wechat: `normalize_wechat_url()`、`fetch_article()`、`build_markdown()`
- github: `fetch_repo()`、`repo_to_markdown()`、`save_repo()`
- papers: `fetch_papers_by_category()`、`paper_to_markdown()`、`save_papers()`
- operator surface: `research/cli.py` dispatch 和参数约束

如果是用户可见行为、输出格式、依赖边界，却没有对应 Requirement，则标记 `no-spec`。

## 4. 一致性检查

- `system.md` 的输出目录规则是否被各域 spec 遵守
- `.ai/L1` 的命令和入口文件是否与 L3 / L5 描述一致
- traceability 中标为 verified 的项，是否真有测试或可重放验证证据

## 5. 测试用例设计（Test Spec）

对 `partial`、`untested`、`missing` 的条目补 test-specs：

- wechat: 优先补纯函数和内容转换边界测试
- github: 优先补 `gh` subprocess mock 测试
- papers: 优先补 XML 解析、类别白名单、文件命名测试
- operator surface: 优先补 `argparse` dispatch、部分成功和输出路径边界测试

测试用例必须包含：

- 具体输入
- 预期输出或文件结果
- 必要的前置条件
- 是否需要 mock 外部依赖

## 验证流程

### 单域验证

```
1. 读 specs/<domain>/spec.md
2. 读对应 L1 feature 文档
3. 定位代码锚点
4. 记录已有测试 / smoke 证据
5. 更新 traceability/<domain>.md
6. 为缺口更新 test-specs/<domain>.md
```

### `.ai` 文档验证

```
1. 对非模板文档运行模板占位词扫描
2. 检查 feature / infrastructure / spec 路径是否存在
3. 抽查命令是否指向 `research/cli.py` 或真实业务层，而非历史占位入口
```

## 可执行验证优先级

1. `.ai` 占位符扫描
2. 根级 `pytest`（如果改到 operator surface、query、briefing、wechat 单测）
3. GitHub / papers 最小 smoke 命令（如果依赖可用）
4. 仅在外部依赖不可用时，退回到 diff + 静态追溯

## 验证报告格式

```markdown
# 验证报告 — <date> (<scope>)

## 概要
- 域: system / wechat / github / papers
- 已验证: N | 部分验证: N | 未验证: N | 缺失: N

## 明细
| Domain | Requirement | Evidence | Status | Notes |
|--------|-------------|----------|--------|-------|

## 待办
1. [ ] 需要新增的测试
2. [ ] 需要修订的 spec
3. [ ] 需要补跑的 smoke 命令
```
