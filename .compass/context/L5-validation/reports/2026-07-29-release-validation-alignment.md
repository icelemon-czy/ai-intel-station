# Release Validation Alignment 报告

## 结论

release validation 已与 Agent-first baseline 对齐。default runtime 保持 lightweight；
optional WeChat、Web 与 package artifact 各自拥有独立 gate。full socket environment
不再依赖 fixed port，也不再用旧 response shape 制造 false failure。

release audit 同时修复一个真实 product gap：arXiv remote failure 过去被转换为 empty list，
Web 会返回 `status=success, item_count=0`。现在 single-category caller 可要求显式
`PapersFetchError`；Web 返回 structured error，discovery 记录 failed category 并继续下一个
category。unknown category、oversized header 和 full-buffer truncation 使用相同 explicit
failure contract，不再被伪装为空成功。

## Red Evidence

### Dependency / suite wiring

```text
dev-only broad pytest:
collection error — tests/test_wechat_collect.py imports bs4 without wechat extra
```

### Full socket + optional environment

```text
417 passed / 12 failed
```

12 failures包含：

- `.Codex/skills` 已退休但 CI 仍强制 mirror。
- fixed ports 与只等待 pre-bind banner 导致 connection race/collision。
- navigation、briefing metadata/content、Collect error 仍断言旧 response shape。
- Papers fixture 第二次创建同一 directory 抛出 `FileExistsError`。

### Product failure reporting

```text
POST /api/collect/run papers + forced remote failure
status=success, item_count=0
```

## Green Evidence

| Gate | Result |
|:-----|:-------|
| Targeted HTTP / response / CI boundary | 151 passed |
| Lightweight core, no WeChat packages | 422 passed, 2 deselected, 3 subtests passed |
| Discovery runner unittest adapter | 15 passed |
| Optional WeChat marker gate | 16 passed, 7 deselected |
| Web Node suite with real loopback | 102 passed, 0 failed, 0 skipped |
| Vite production build | 33 modules transformed |
| Skill lint + YAML parse | PASS；5 workflow jobs parsed |
| Python build | wheel + sdist built |
| Artifact checker | PASS；`index.html` 引用的 hashed JS/CSS 均存在，private runtime paths absent |
| Isolated wheel CLI | `research --help` PASS；CI 自动安装 wheel 后重验 |
| Isolated wheel Web | real loopback `/` 与全部 referenced assets 返回非空 200；CI 自动重验 |
| Review blocker regression | Papers / artifact / Web service 17 passed；discovery runner 15 passed |
| Test isolation regression | mixed-category real subprocess 1 passed；full core 422 passed 后 repository output/state 无 dirty file |
| Single-context cleanup | 240-file `.ai` + retired mirrors + absolute local symlinks removed；13 targeted + skill lint + 422 core PASS |
| Compass 0.4.0 footprint | staging 只剩 `context/`；9 Workflow 除 documented `build-context` installed-state fix 外与 sibling source 对齐 |
| Portable platform config | tracked Claude launch 不再包含前开发者 `/Users/...` path；repo-relative runtime/output regression verified |

## Boundary Decisions

- `.agents/skills` 是 canonical project Workflow；`.github/.claude` 仅保留
  daily-discovery adapter，不再做全树 mirror。
- user review 后删除已合并的 240-file `.ai` snapshot、legacy Codex Skills 与 retired
  GitHub/Claude Workflow mirrors；原文继续存在于 Git history，不进入 active context。
- core CI 不安装 browser stack；需要 optional runtime 的 test 使用 `wechat` marker。
- `tests/test_discovery_runner.py` 的 module-level compatibility functions 只通过 unittest
  adapter 运行，避免 pytest 把 `self` 当 fixture 再收集一次。
- remote source test 使用 local network fixture 与 temporary output；不得因 operator/CI
  网络恰好可用而把 live material 写入 repository archive。
- WeChat live e2e 仍需 operator 明确提供 `WECHAT_E2E_URLS`；本报告不冒充 live fetch
  成功。
- Web 是 optional viewer，但 wheel 既然暴露 `research web`，就必须包含 built static。
- release artifact gate 必须安装 wheel，并从 installed package 启动 real loopback smoke；
  仅检查 archive filename 不构成运行证据。

## Traceability

- Collection `Source-Specific Validation and Errors`：verified。
- Collection / Papers category failure isolation：verified。
- Research Operations lightweight core、optional runtime 与 Local Web entry：verified。
- System documented entrypoint / release artifact：verified。
