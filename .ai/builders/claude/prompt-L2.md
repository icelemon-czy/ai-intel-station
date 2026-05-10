# Claude 构建 L2 编码规则 — Prompt 模板

> 将以下 prompt 复制到 Claude 对话中使用。
> 使用前替换 `[项目目录]` 和 `[模块名]` 为实际值。
>
> **前置条件**: 已用 `prompt-L1a.md` + `prompt-L1b.md` 完成 L1 文档生成。
> 如果在同一对话中继续，Phase 1-2 的分析数据可直接复用。
> 如果在新对话中开始，需要先快速重新收集信息（见下方 Phase 0）。

---

## Prompt

```markdown
# 任务：构建项目编码规则（L2）

## 背景
我需要为本项目构建 AI 上下文文档中的 **L2 编码规则层**。模板在：
- `.ai/L2-rules/global.md` — 全局规则（命名、错误处理、反模式等）
- `.ai/L2-rules/templates.md` — 新建文件的代码模板
- `.ai/L2-rules/_module-template.md` — 模块规则模板（复制为 `[模块名].md`）

L1 导航文档已经完成，在 `.ai/L1-codebase-map/` 下。

## 核心原则
- ✅ L2 规则要从代码中的**实际模式**提取，不要编造项目没在用的规范
- ❌ 不要写 "使用 Repository 模式"（除非代码里真的在用）
- ✅ 每条规则给出 ✅ 正确写法和 ❌ 错误写法的具体代码示例
- ✅ 不确定的地方标 `[待人工确认]`，不要猜测

## 你的工作步骤

### Phase 0（仅新对话需要）: 快速重建上下文

> 如果在 L1 同一对话中继续，跳过此步骤，直接进入 Phase 4。

```bash
# 快速获取项目结构（3 层深度）
find . -maxdepth 3 -not -path '*/node_modules/*' -not -path '*/.git/*' -not -path '*/dist/*' -not -path '*/__pycache__/*' -not -path '*/venv/*' -not -path '*/.venv/*' -not -path '*/build/*' -not -path '*/target/*' | head -120 | sort

# 读取已完成的 L1 文档（了解模块划分和数据流）
cat [项目目录]/.ai/L1-codebase-map/overview.md
cat [项目目录]/.ai/L1-codebase-map/module-map.md

# 重新收集 import 关系（L2 需要用
grep -rn "import\|from\|require" --include='*.ts' --include='*.py' --include='*.java' --include='*.go' | head -100

# Lint / 格式化配置
cat .eslintrc* tsconfig.json .prettierrc* pyproject.toml setup.cfg .golangci.yml 2>/dev/null

# export / 公开 API
grep -rn "^export\|module\.exports\|__all__" --include='*.ts' --include='*.py' --include='*.js' | head -80

# TODO/FIXME/HACK
grep -rn "TODO\|FIXME\|HACK\|WARN\|DEPRECATED\|LEGACY" --include='*.ts' --include='*.py' --include='*.java' --include='*.go' | head -50
```

### Phase 4: 提取全局规则（→ L2-rules/global.md）

读取 `.ai/L2-rules/global.md` 模板，然后从代码中提取以下信息来填写：

#### 4a: 技术栈与构建命令
- 从 `package.json` / `pyproject.toml` / `go.mod` / `pom.xml` 提取语言版本、框架、依赖
- 从 `scripts` / `Makefile` / CI 配置提取构建、测试、lint 命令

#### 4b: 命名约定
统计项目中实际使用的命名模式（不要编造项目没在用的规范）：
```bash
# 文件名模式
ls src/**/*.ts src/**/*.py 2>/dev/null | head -20

# 类名 / 函数名模式
grep -rn "^class \|^export class \|^def \|^func \|^function " --include='*.ts' --include='*.py' --include='*.go' | head -30
```
根据统计结果判断：文件名是 kebab-case 还是 camelCase？类名是 PascalCase？函数名是什么风格？

#### 4c: 依赖方向规则
从 import 分析中提取：
- 哪些目录之间存在 import 关系？哪些不存在？
- 推断出允许/禁止的依赖方向
- 从 ESLint 的 `import/no-restricted-paths` 或类似规则验证

#### 4d: 错误处理模式
在代码中搜索错误处理相关的模式：
```bash
# 自定义错误类
grep -rn "extends Error\|class.*Error\|class.*Exception" --include='*.ts' --include='*.py' --include='*.java' | head -20

# 全局错误处理
grep -rn "errorHandler\|error_handler\|@ExceptionHandler\|recover()" --include='*.ts' --include='*.py' --include='*.java' --include='*.go' | head -10

# catch 模式
grep -rn "catch\|except\|rescue" --include='*.ts' --include='*.py' --include='*.rb' | head -20
```
从实际代码中提取：用了哪些错误类？在哪层 catch？返回什么格式？

#### 4e: 反模式清单
从 lint 配置中提取禁用的规则，转换为人可读的反模式：
```bash
# ESLint 禁用规则
grep -A 2 '"error"\|"warn"' .eslintrc* 2>/dev/null | head -30

# 项目中的 eslint-disable 注释（说明有人违反过规则）
grep -rn "eslint-disable\|noqa\|noinspection\|@SuppressWarnings" --include='*.ts' --include='*.py' --include='*.java' | head -20
```

#### 4f: 新建文件模板（→ templates.md）
找到 3+ 个同类型的文件（如 service、controller、test），提取它们的公共结构作为模板，**写入 `templates.md`（不是 global.md）**：
```bash
# 对比多个 service 文件的开头结构
head -30 src/services/*.ts src/**/service.ts 2>/dev/null
head -30 src/**/*.service.ts 2>/dev/null

# 对比多个测试文件的结构
head -30 src/**/*.test.ts tests/*.py 2>/dev/null
```

#### 4g: 版本控制规范
```bash
# 从 git log 推断 commit 格式
git log --oneline -20 2>/dev/null

# 从分支名推断命名规范
git branch -a 2>/dev/null | head -20
```
判断：是 Conventional Commits？分支名用 `feat/` `fix/` 前缀？

#### 4h: 测试规范（→ L2-rules/testing.md）
从测试文件中提取，**写入 `testing.md`（不是 global.md）**：

```bash
# 测试框架（从依赖推断）
cat package.json pyproject.toml go.mod 2>/dev/null | grep -i "jest\|mocha\|vitest\|pytest\|testify\|junit\|playwright\|cypress"

# 测试文件分布和命名
find . -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*' -o -name '*_test.*' 2>/dev/null | head -20

# 测试配置
cat jest.config* vitest.config* pytest.ini conftest.py 2>/dev/null | head -60

# 抽样 2-3 个测试文件结构
head -30 src/**/*.test.ts tests/*.py 2>/dev/null
```

读取 `.ai/L2-rules/testing.md` 模板，根据扫描结果填写：
- 测试框架 + 运行命令
- 文件命名和位置约定
- 单元测试：隔离策略、mock 工具、断言风格、数据构造
- 集成测试：数据库策略、外部服务 mock
- UI 测试（如有）：选择器策略、等待机制
- 覆盖率要求
- 反模式

**填写 global.md 时的规则**：
- 只写从代码中实际观察到的规范，不要假设或编造
- 能从 lint 配置自动验证的规则，标注验证方式
- 不确定的地方标 `[待人工确认：观察到 xxx，但不确定是否是有意为之]`
- 新建文件模板写入 `templates.md`，不要放在 global.md

### Phase 5: 为每个模块生成规则文件（→ L2-rules/[module].md）

对 L1 module-map.md 中识别出的每个主要模块，复制 `.ai/L2-rules/_module-template.md`，重命名为模块名，填写以下内容：

> 💡 如果项目较大（模块 > 5 个），可以分批处理：本次对话处理 2-3 个模块，剩余的开新对话。

#### 对每个模块执行：

**5a: 公开 API 清单**
```bash
# 找到该模块所有的 export
grep -rn "^export" src/[模块名]/ --include='*.ts' | head -30

# 或 Python
grep -rn "^def \|^class " src/[模块名]/ --include='*.py' | head -30
```
列出所有 export 的函数/类，标注：
- ✅ STABLE — 被 2+ 个外部模块 import（从 import 分析中可以看出）
- 🔧 INTERNAL — 只在模块内部调用

**5b: 模块边界**
```bash
# 谁 import 了这个模块？
grep -rn "from.*[模块名]\|import.*[模块名]" --include='*.ts' --include='*.py' | grep -v "[模块名]/" | head -20

# 这个模块 import 了谁？
grep -rn "from\|import" src/[模块名]/ --include='*.ts' --include='*.py' | grep -v "node_modules\|from '\." | head -20
```
从 import 关系推断：
- 哪些模块可以调用本模块？（实际有 import 的）
- 本模块依赖了哪些其他模块？
- 有没有可疑的依赖？（如 domain 层 import 了 infrastructure）

**5c: 测试策略**
```bash
# 该模块的测试文件
find src/[模块名] -name "*.test.*" -o -name "*_test.*"
ls tests/[模块名]/ 2>/dev/null

# 测试中 mock 了什么
grep -rn "mock\|Mock\|patch\|stub\|spy" src/[模块名]/**/*.test.* tests/[模块名]/ 2>/dev/null | head -20
```

**5d: 已知陷阱**
```bash
# 模块内的 TODO/FIXME/HACK
grep -rn "TODO\|FIXME\|HACK\|WARN\|DEPRECATED\|LEGACY\|XXX" src/[模块名]/ | head -20

# 可疑的硬编码
grep -rn "hardcode\|magic.*number\|env\[.*\]\|process\.env\|os\.environ" src/[模块名]/ | head -10

# 环境判断逻辑（可能有隐式行为）
grep -rn "NODE_ENV\|RAILS_ENV\|DEBUG\|PRODUCTION\|STAGING" src/[模块名]/ | head -10
```

**5e: 需要人工确认的字段**
以下字段 AI 无法从代码确定，标记 `[待人工确认]`：
- **模块状态**：从 git log 推断活跃度，但 stable/active/legacy 的判断需要人确认
  ```bash
  git log --oneline --since="3 months ago" -- src/[模块名]/ | wc -l
  ```
  标注：`[待人工确认：最近 3 个月有 N 次 commit，推测为 active，请确认]`
- **使用规则中的隐式合约**：如 "调用 requireAuth() 后 req.user 上会有什么"，需要人补充
  标注：`[待人工确认：从代码中看到 req.user 被赋值了 {id, role}，但不确定是否还有其他字段]`
- **依赖禁止的原因**：能发现"A 没有 import B"，但"为什么禁止"需要人填
  标注：`[待人工确认：当前代码中 auth 没有 import payment，是否应该禁止？]`

**填写模块规则时的规则**：
- 只为主要模块生成规则文件（通常 3-8 个），不要为每个子目录都生成
- 公开 API 清单只列被外部实际调用的函数，不要把所有 export 都列出来
- 模块边界表基于实际的 import 关系，不要推测

### 约束
- 每个文档控制在合理长度
- 不确定的地方写 `[待确认：xxx]`，不要编造
- 如果某处关系复杂看不清，标注 `[需要深入分析：xxx]`
- **检验标准**：每条规则都问"这是从代码实际观察到的吗？"如果不是，删掉
```

---

## 补充说明

### 质量检验清单

填完后用以下标准审查每一行内容：

| 检查项 | 通过标准 | 不通过的例子 |
|--------|----------|-------------|
| 是否来自代码？ | 规则基于实际代码中观察到的模式 | ❌ "使用 Repository 模式"（但代码里没有） |
| 是否可执行？ | AI 能直接照做 | ❌ "保持代码整洁" |
| 有正反例？ | 有具体的✅正确和❌错误示例 | ❌ "命名用 camelCase"（没有示例） |
| 人工标记完整？ | 不确定的字段都已标 `[待人工确认]` | ❌ 猜测模块状态为 stable（但没有标记） |

### Subagents 使用指南

主 Agent（Claude Code）做 80% 的分析工作，subagents 只在需要深入时使用：

```
主 Agent（Claude Code）
├── Phase 4a-4c：自己从配置文件和 import 分析中提取规则
├── Phase 4d-4e：自己从代码中搜索错误处理和反模式
├── Phase 4f-4h：自己提取模板、版本控制、测试规范
├── 填写 global.md
├── Phase 5：逐个处理每个主要模块
│     ⚠️ 如果某个模块特别大（50+ 个 export）或内部结构复杂：
│     └── 【subagent】“请分析 src/[模块]/ 的所有 export，列出函数签名 + 被谁调用”
│     ☸️ 如果需要深入理解一个模块的内部依赖关系：
│     └── 【subagent】“请画出 src/[模块]/ 内部各文件的 import 关系图”
└── 最终：汇总所有 [待人工确认] 标记，提醒用户审核
```

**何时用 subagents**:
- 某个模块 export 数量多（50+），需要分析每个函数的调用者
- 模块内部文件关系复杂，需要单独理清

**不要用 subagents**:
- 执行 Phase 0/4 的 grep/cat 命令（主 Agent 直接跑）
- 填写模板文件（主 Agent 自己填）

### 工作量预期

| 阶段 | 输出 | 建议 |
|------|------|------|
| Phase 4 (全局规则) | global.md | 紧接 L1 之后，同一对话完成 |
| Phase 5 (模块规则) | 3-8 个 [module].md | 模块 ≤ 5 个：同对话完成；> 5 个：拆成多次对话，每次 2-3 个模块 |

### 人工审核清单

Claude 完成后，你需要审核所有 `[待人工确认]` 标记。常见需要确认的点：

- **模块状态判断** — Claude 从 git log 推断活跃度，但你要确认 stable/active/legacy
- **依赖禁止原因** — Claude 能发现"A 没有 import B"，但"为什么禁止"需要你补充
- **隐式合约** — 如 "调用 authenticate() 后返回的 token 包含哪些字段"
- **反模式的 why** — Claude 从 lint 规则提取了禁止项，你可能需要补充原因
- **新建文件模板** — Claude 从现有代码提取了模式，确认这是你想要的标准

### 从旧版模板迁移（L2 部分）

如果项目已有旧版文档（描述性内容），可以这样迁移：

1. **保留**：已有的具体规则（如果是从实际代码中来的）
2. **删除**：抽象声明（如 "架构模式: Clean Architecture"）
3. **新增**：反模式清单、新建文件模板、模块陷阱、变更联动原因
4. **补充**：所有规则加上正确/错误示例
