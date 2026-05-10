---
name: setup-testing
description: "Set up or update project testing conventions in L2-rules/testing.md. Use when: 测试规范, testing rules, 配置测试, setup tests, 更新测试规范, test conventions, 怎么写测试, how to test"
argument-hint: "Optional: specific area to update (e.g., 'UI testing', 'mock strategy', 'coverage')"
---

# Setup Testing Conventions

读取项目代码推断测试框架和模式，引导用户确认，生成或更新 `.ai/L2-rules/testing.md`。

## Prerequisites

- `.ai/` 目录已存在
- 项目中有代码（不一定已有测试）

## Procedure

---

### Step 1: 扫描项目测试现状

```bash
# 测试框架（从依赖文件推断）
cat package.json pyproject.toml go.mod pom.xml Cargo.toml 2>/dev/null | grep -i "jest\|mocha\|vitest\|pytest\|unittest\|testify\|junit\|playwright\|cypress\|selenium"

# 测试文件分布
find . -name '*.test.*' -o -name '*.spec.*' -o -name 'test_*' -o -name '*_test.*' 2>/dev/null | head -20

# 测试配置
cat jest.config* vitest.config* pytest.ini conftest.py .nycrc* 2>/dev/null | head -60

# 测试运行命令
cat package.json 2>/dev/null | grep -A 5 '"test"'
cat Makefile 2>/dev/null | grep -A 2 'test'

# 抽样读取 2-3 个测试文件的结构
```

### Step 2: 读取现有 testing.md（如存在）

```bash
cat .ai/L2-rules/testing.md 2>/dev/null
```

如不存在，读取项目模板库中的 `L2-rules/testing.md` 模板（路径：`.ai/L2-rules/_module-template.md` 或 project-compass 仓库的 `L2-rules/testing.md`），了解期望的章节结构，然后基于此格式创建。

### Step 3: 生成初稿 / 更新

**有参数（更新特定区域）**：只修改 testing.md 中对应的章节。

**无参数（全量生成/更新）**：

根据 Step 1 扫描结果，填写 testing.md 的每个章节。规则：

- ✅ 从代码中实际观察到的模式提取，不编造
- ✅ 有多种做法时，按以下优先级选择：① 项目 lint/config 中显式配置的 → ② `package.json`/`pyproject.toml` 依赖中安装了的 → ③ 测试文件中实际使用次数最多的（`grep -rc 'import.*from' <test-dir> | sort -t: -k2 -rn | head`）。如果三者冲突，以 ① 为准
- ❌ 不确定的地方标 `[待确认]`，但必须附上不确定的原因（如"代码中同时使用了 jest 和 vitest，无法判断哪个是主框架"）。`[待确认]` 总数不得超过 3 个；超过则说明扫描不充分，需要回到 Step 1 补充扫描

### Step 4: 展示给用户确认

展示生成的 testing.md 内容摘要，**逐章节**向用户提出确认问题：

```
## 测试规范预览

### 测试框架
检测到：Jest (单元) + Playwright (E2E)
运行命令：`npm test` / `npx playwright test`
→ 正确吗？有补充吗？

### 测试文件约定
检测到：`*.test.ts`，与源文件同目录
→ 正确吗？

### 单元测试规范
检测到：jest.mock() 隔离外部依赖，expect 断言
→ 有特殊的 mock 策略吗？（如 MSW、手写 fake 等）

### UI 测试规范
检测到：data-testid 选择器，auto-waiting
→ 有额外约定吗？

### 覆盖率
未检测到覆盖率配置
→ 有覆盖率要求吗？（如 80%、仅核心模块等）

### 反模式
从代码中观察到 [N] 个潜在反模式
→ 要加入禁止清单吗？
```

**等用户回答后更新 testing.md。**

### Step 5: 写入文件

将最终内容写入 `.ai/L2-rules/testing.md`。

如果是更新（文件已存在），只修改变更的章节，保留其他内容不变。

---

### 输出格式

```
## 测试规范已更新

### 变更内容
| 章节 | 操作 |
|------|------|
| 测试框架 | 新建 / 更新 / 未变 |
| 单元测试 | 新建 / 更新 / 未变 |
| ...  | ... |

文件位置：`.ai/L2-rules/testing.md`

后续写测试时，new-change / continue-change / fix-bug 会自动加载此规范。
```
