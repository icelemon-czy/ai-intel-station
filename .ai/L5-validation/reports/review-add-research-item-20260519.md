# 测试审查报告: add-research-item

## 本次审查目标

- 类型: change
- 名称: add-research-item
- 优先级来源: P1 pending-review
- 队列剩余: 4 项未审，下次调用将审查 add-research-operator-surface

## 测试规范

- 测试框架: pytest
- 测试目录: `tests/`
- 规范命令: `uv run --with pytest python -m pytest tests/test_research_item.py tests/test_restructure_research_architecture.py tests/test_wechat_collect.py`
- 本次相关测试: `python3 -m pytest tests/test_research_item.py`

## 执行结果

- 测试运行: `tests/test_research_item.py` 4 passed
- 规范命令复现: `uv run --with pytest python -m pytest tests/test_research_item.py` 因 sandbox 无法访问 `/Users/chansteven/.cache/uv/sdists-v9/.git` 未完成；提权自动审批超时。本次使用已安装依赖的 `python3 -m pytest tests/test_research_item.py` 完成目标文件验证。
- 异常标记: 相关文件无 `.skip` / `.only` / pending 标记
- 审查范围: `.ai/L3-specs/changes/add-research-item/specs/*/spec.md`
- 结论: ❌ 打回

## 主表

| # | Req | Scenario | Spec THEN | 测试函数 | 测试文件:行 | 实际 assertion | 调用链验证 | 反模式命中 | 反向推理 | 结论 |
|---|-----|----------|-----------|----------|-------------|----------------|------------|------------|------------|------|
| 1 | Unified ResearchItem Schema | Normalize a GitHub repository snapshot | the system can represent it as a `ResearchItem` with source, item type, title, canonical URL, summary, timestamps, tags, and source-specific metadata | `test_build_github_repo_item_normalizes_repository_metadata` | `tests/test_research_item.py:31` | `source == "github"`, `item_type == "repository"`, `title == "claude-code"`, `canonical_url == ...`, `summary == ...`, `tags == ["agent", "cli"]`, owner/repo/output path | ✅ 真实调用 `build_github_repo_item()` | 🔴 #5 assertion 未覆盖 timestamps、stargazer_count、primary_language、issue_count | ⚠️ 删除 timestamp/部分 metadata 赋值仍可能绿 | 🔴 |
| 2 | Unified ResearchItem Schema | Normalize a paper summary | the system can represent it as a `ResearchItem` with title, authors, abstract summary, URLs, timestamps, and categories | `test_parse_existing_output_samples_into_research_items` | `tests/test_research_item.py:79` | `paper_item.source == "papers"`, `item_type == "paper"`, `canonical_url == ...` | ✅ 真实调用 `parse_paper_markdown()` | 🔴 #5 assertion 未覆盖 title/authors/summary/timestamps/categories | 🔴 删除 authors/summary/category 解析仍会绿 | 🔴 |
| 3 | Unified ResearchItem Schema | Normalize a WeChat article | the system can represent it as a `ResearchItem` with title, source URL, publisher or author when available, publish time when available, and summary body metadata | `test_build_wechat_item_allows_missing_optional_fields` / `test_parse_existing_output_samples_into_research_items` | `tests/test_research_item.py:60` / `tests/test_research_item.py:79` | source/item_type/title/canonical_url/authors/published_at; parse sample source/item_type/url | ✅ 真实调用 `build_wechat_item()` 和 `parse_wechat_markdown()` | 🔴 #5 未覆盖 summary body metadata | 🔴 删除 body summary metadata 仍可能绿 | 🔴 |
| 4 | Partial ResearchItems Are Allowed | Missing optional metadata | the system still emits a valid `ResearchItem` with empty or null optional fields instead of failing the whole item | `test_build_wechat_item_allows_missing_optional_fields` | `tests/test_research_item.py:60` | `authors == []`, `published_at is None` | ✅ 真实调用 `build_wechat_item()` | 🔴 #5 未断言 optional tag list 空值降级，也未覆盖 JSON validity | ⚠️ 删除 tags 默认值相关行为可能仍绿 | 🔴 |
| 5 | Sidecar Persistence Within Source Directories | Persist a repo-side sidecar | the output directory contains the existing Markdown file and a `research-item.json` sidecar in the same source directory | ❌ 缺失 | — | — | — | ❌ 无 `save_repo()` 文件系统测试 | — | 🔴 |
| 6 | Sidecar Persistence Within Source Directories | Persist a search-side sidecar set | the search output directory contains the existing `search.md` file and a `research-items.jsonl` sidecar for the normalized result items | ❌ 缺失 | — | — | — | ❌ 无 `save_search_results()` 文件系统测试 | — | 🔴 |
| 7 | Sidecar Persistence Within Source Directories | Persist a paper-side sidecar | the same source directory contains a `<stem>.research-item.json` sidecar for that paper | ❌ 缺失 | — | — | — | ❌ 无 `save_papers()` 文件系统测试 | — | 🔴 |
| 8 | Sidecar Persistence Within Source Directories | Persist a WeChat article sidecar | the same article directory contains a `research-item.json` sidecar | ❌ 缺失 | — | — | — | ❌ 无 `fetch_article()` 或等价命令级 sidecar 测试 | — | 🔴 |
| 9 | Historical Output Backfill | Backfill historical outputs | normalized sidecar files are written for all parseable historical items while preserving the existing Markdown files | `test_backfill_output_tree_writes_expected_sidecars` | `tests/test_research_item.py:103` | sidecar paths in `written`; repo/search/paper/wechat payload source/item_type basics | ✅ 真实调用 `backfill_output_tree()` | 🔴 #5 未断言 existing Markdown files preserved | 🔴 backfill 删除 Markdown 文件后测试仍可能绿 | 🔴 |
| 10 | Persist ResearchItem Sidecars For GitHub Outputs | Generate one repository snapshot | the tool writes the existing `README.md` and a `research-item.json` sidecar under `output/github/<owner-repo>/` | ❌ 缺失 | — | — | — | ❌ 无 `save_repo()` 测试 | — | 🔴 |
| 11 | Persist ResearchItem Sidecars For GitHub Outputs | Generate one search result set | the tool writes the existing `search.md` and a `research-items.jsonl` sidecar under `output/github/<query>/` | ❌ 缺失 | — | — | — | ❌ 无 `save_search_results()` 测试 | — | 🔴 |
| 12 | Persist ResearchItem Sidecars For Paper Outputs | Generate one paper Markdown file | the tool also writes a `<stem>.research-item.json` sidecar in the same directory | ❌ 缺失 | — | — | — | ❌ 无 `save_papers()` 测试 | — | 🔴 |
| 13 | Persist ResearchItem Sidecars For Article Outputs | Generate one WeChat article output | the article directory contains the existing Markdown artifact, the existing `images/` directory when applicable, and a `research-item.json` sidecar | ❌ 缺失 | — | — | — | ❌ 无 `fetch_article()` sidecar/images 断言；live e2e 仅验证 Markdown/source URL | — | 🔴 |

## 逐测试函数反模式检查

### `tests/test_research_item.py:31` — `test_build_github_repo_item_normalizes_repository_metadata`

对应 Scenario: Unified ResearchItem Schema / Normalize a GitHub repository snapshot

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 9 个 `assert` |
| 2 | 断言太弱 | ✅ 通过 | 均为具体字段值比较 |
| 3 | Happy path only | 🔴 命中 | 同 Requirement 下 paper/wechat 有测试，但 GitHub metadata 缺少缺字段/边界场景 |
| 4 | Mock 被测函数 | ✅ 通过 | 直接调用真实 `build_github_repo_item()` |
| 5 | 绕开 THEN | 🔴 命中 | Spec 要求 timestamps 和 source-specific metadata，测试未断言 `published_at`、`updated_at`、stars/language/issue_count |
| 6 | 条件永真 | ✅ 通过 | 未发现自证断言 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |
| 8 | 用真实网络代替纯函数测试 | ✅ 通过 | 无网络 |
| 9 | live e2e 配置误判 | ✅ 通过 | 不适用 |
| 10 | smoke 只看 print | ✅ 通过 | 不适用 |
| 11 | 为测试改 output 样例 | ✅ 通过 | 未修改样例 |

### `tests/test_research_item.py:60` — `test_build_wechat_item_allows_missing_optional_fields`

对应 Scenario: Partial ResearchItems Are Allowed / Missing optional metadata

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 6 个 `assert` |
| 2 | 断言太弱 | ✅ 通过 | 断言具体字段或 `None` |
| 3 | Happy path only | 🔴 命中 | 只覆盖 WeChat author/publish_time 缺失，未覆盖 optional tag list |
| 4 | Mock 被测函数 | ✅ 通过 | 直接调用真实 `build_wechat_item()` |
| 5 | 绕开 THEN | 🔴 命中 | Spec 要求 empty/null optional fields，测试未断言 `tags == []` 或 JSON payload validity |
| 6 | 条件永真 | ✅ 通过 | 未发现自证断言 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |
| 8 | 用真实网络代替纯函数测试 | ✅ 通过 | 无网络 |
| 9 | live e2e 配置误判 | ✅ 通过 | 不适用 |
| 10 | smoke 只看 print | ✅ 通过 | 不适用 |
| 11 | 为测试改 output 样例 | ✅ 通过 | 未修改样例 |

### `tests/test_research_item.py:79` — `test_parse_existing_output_samples_into_research_items`

对应 Scenario: Normalize paper/wechat samples and parse historical outputs

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 13 个 `assert` |
| 2 | 断言太弱 | ✅ 通过 | 主要为具体字段值或 startswith URL |
| 3 | Happy path only | 🔴 命中 | 样例解析只覆盖 happy path，缺字段/异常样例未覆盖 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 parse 函数 |
| 5 | 绕开 THEN | 🔴 命中 | paper/wechat normalization 只断言 source/type/url，未覆盖 authors/summary/time/categories/body metadata |
| 6 | 条件永真 | ✅ 通过 | 未发现自证断言 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |
| 8 | 用真实网络代替纯函数测试 | ✅ 通过 | 使用本地样例 |
| 9 | live e2e 配置误判 | ✅ 通过 | 不适用 |
| 10 | smoke 只看 print | ✅ 通过 | 不适用 |
| 11 | 为测试改 output 样例 | ✅ 通过 | 未修改样例 |

### `tests/test_research_item.py:103` — `test_backfill_output_tree_writes_expected_sidecars`

对应 Scenario: Historical Output Backfill / Backfill historical outputs

| # | 反模式 | 结果 | 证据 |
|---|--------|------|------|
| 1 | 断言缺失 | ✅ 通过 | 10 个 `assert` |
| 2 | 断言太弱 | ✅ 通过 | 断言具体路径、长度、source/type |
| 3 | Happy path only | 🔴 命中 | 只覆盖 parseable happy path，未覆盖不可解析或缺来源目录 |
| 4 | Mock 被测函数 | ✅ 通过 | 真实调用 `backfill_output_tree()` |
| 5 | 绕开 THEN | 🔴 命中 | Spec 要求 preserving existing Markdown files，测试未断言 Markdown 文件仍存在且内容未变 |
| 6 | 条件永真 | ✅ 通过 | 未发现自证断言 |
| 7 | 吞异常 | ✅ 通过 | 无 try/catch |
| 8 | 用真实网络代替纯函数测试 | ✅ 通过 | 使用 `tmp_path` 和本地样例 |
| 9 | live e2e 配置误判 | ✅ 通过 | 不适用 |
| 10 | smoke 只看 print | ✅ 通过 | 检查了文件内容，不只看输出 |
| 11 | 为测试改 output 样例 | ✅ 通过 | 未修改样例 |

## 覆盖概要

| 能力域 | Requirement | Scenario | ✅ 有效 | 🔴 缺陷 | ❌ 缺失 |
|--------|-------------|----------|--------|---------|---------|
| research-item | 4 | 9 | 0 | 5 | 4 |
| github | 1 | 2 | 0 | 0 | 2 |
| papers | 1 | 1 | 0 | 0 | 1 |
| wechat | 1 | 1 | 0 | 0 | 1 |

## 反模式统计

| 反模式 | 命中次数 | 涉及测试 |
|--------|----------|----------|
| #3 Happy path only | 4 | `test_build_github_repo_item_normalizes_repository_metadata`, `test_build_wechat_item_allows_missing_optional_fields`, `test_parse_existing_output_samples_into_research_items`, `test_backfill_output_tree_writes_expected_sidecars` |
| #5 Assertion 绕开 Spec THEN | 4 | 同上 |
| ❌ Scenario 无测试 | 8 | repo/search/paper/wechat runtime sidecar persistence scenarios |

## 覆盖缺口

| 类型 | 描述 | 建议 |
|------|------|------|
| 缺失 Scenario 测试 | `collect.github.save_repo()` 没有 tmp_path + mocked `fetch_repo()` 文件系统测试 | 补测试断言 `README.md` 与 `research-item.json` 同目录生成，并校验 sidecar 关键字段 |
| 缺失 Scenario 测试 | `collect.github.save_search_results()` 没有 tmp_path 文件系统测试 | 补测试断言 `search.md`、`research-items.jsonl`、query 空格目录名和 JSONL 内容 |
| 缺失 Scenario 测试 | `collect.papers.save_papers()` 没有 tmp_path 文件系统测试 | 补测试断言 paper Markdown 与 `<stem>.research-item.json` 同目录生成 |
| 缺失 Scenario 测试 | `collect.wechat.fetch_article()` 没有可控依赖下的 sidecar/images 断言 | 可拆纯 helper 或 monkeypatch browser/download，断言 Markdown、images 目录和 `research-item.json` |
| Assertion 缺口 | normalization 测试未完整覆盖 Spec THEN 字段 | 补充 GitHub timestamps/source metadata、paper authors/summary/time/categories、WeChat body summary metadata、optional tags |
| Assertion 缺口 | backfill 未断言 Markdown preservation | 在 backfill 后断言原 Markdown 文件仍存在且内容未变 |

## 结论

- [ ] ✅ 通过
- [ ] ⚠️ 有缺口但非阻塞
- [x] ❌ 打回

## 打回原因

1. 🔴 `tests/test_research_item.py:31` 反模式 #5: GitHub normalization 未完整断言 Spec THEN 中的 timestamps/source-specific metadata。
2. 🔴 `tests/test_research_item.py:79` 反模式 #5: paper/wechat normalization 未完整断言 authors/summary/timestamps/categories/body metadata。
3. 🔴 `tests/test_research_item.py:103` 反模式 #5: backfill 测试未断言 existing Markdown files 被保留。
4. ❌ `Sidecar Persistence Within Source Directories` 多个 Scenario 无测试: 缺少 `save_repo()`、`save_search_results()`、`save_papers()`、`fetch_article()` 的直接 runtime sidecar 持久化测试。

## 循环状态

- 本次已审查: change/add-research-item
- 本次结论: ❌ 打回
- 队列剩余: 4 项
- 下次调用将审查: add-research-operator-surface
