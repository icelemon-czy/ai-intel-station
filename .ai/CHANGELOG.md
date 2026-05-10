# Changelog

本项目对 `.github/skills/`、`entrypoints/`、`L*` 模板都视为**公共接口**。fork 使用者请按本文件判断是否需要 rebase。

版本号采用 [Semantic Versioning](https://semver.org/)：

- **MAJOR** — skill 改名、状态机不兼容变更、模板字段重命名
- **MINOR** — 新增 skill / 新增字段 / 可选能力
- **PATCH** — 措辞修订、拼写、语义不变的澄清

## [0.3.0] — 2026-04-18

### BREAKING
- **`/spec-fix` 改名为 `/fix-bug`**，并内置 5 类分诊（代码 / 测试 / 虚假通过 / Spec 歧义 / Spec 缺失）。fork 用户需要把对 `/spec-fix` 的引用替换为 `/fix-bug`。
- **proposal.md 模板新增必填字段**：`parent-change`、`depth`。旧模板生成的 proposal 可留空，但新 skill 期望这两个字段存在。

### Added
- `/review-tests` Step 0：**强制执行项目测试套件**。红灯直接转 `/fix-bug`，不得在失败状态下走审查。
- `/review-tests` Step 3：**7 条虚假通过反模式清单**（断言缺失 / 断言太弱 / Happy path only / Mock 了要测的东西 / Assertion 绕开 spec THEN / 条件永真 / 吞异常）。项目可在 `L2-rules/testing.md` 追加第 8+ 条。
- `/fix-bug` Step 3C：**递归环检测**，`depth >= 2` 时不再创建嵌套 fix 变更。
- `/new-change` Step 7：**强制读取 L2 rules** 并在输出中列出本次要遵守的关键规则。
- `/continue-change` Step 2a：**L4 session 漂移检查**，session 与 git/tasks 不一致时必须先对齐再续写。
- `/update-ai` Step 2：明确标注 `git diff` 是启发式，Step 3 必须由用户逐条确认。
- `/archive-change` Step 3：MODIFIED 区段合并示例（整块替换规则）。
- `/build-ai`：明确对 `builders/*.md` 的版本依赖，缺失时停止而不是自造。
- `proposal.md` 模板：允许状态转移表 + append-only 转移日志。
- `README` / `README.zh`：专门的 Skill 章节，含 skill 发现机制说明（Claude Code 原生、Copilot 指令驱动）。
- `VERSION` + 本 `CHANGELOG.md`。
- `.github/workflows/validate.yml`：最小 CI（SKILL.md 单 front-matter 校验、无 `13 skills` 字样残留）。
- `L5-validation/traceability/_example.md`：一个填好的追溯示例。

### Changed
- 统一使用 **12 skills** 口径（之前文档错误标注为 13）。
- "唯一人工门槛" 措辞更正为 **两个关键人工门槛（Proposal + Review）+ 少量轻确认**。
- README 中 skill 流程图改为 mermaid，避免 ASCII 在中英混排下对齐错位。

### Fixed
- **P0**：`.github/skills/fix-bug/SKILL.md` 与 `.github/skills/review-tests/SKILL.md` 末尾残留旧版本 front-matter + 正文，YAML 解析会被污染。已移除。

## [0.2.0] — 2026-04-17
- 首版 `/spec-fix`、`/review-tests`（静态审查）、`/archive-change`。

## [0.1.0] — 2026-04
- 初始 5 层架构 + builder prompts。
