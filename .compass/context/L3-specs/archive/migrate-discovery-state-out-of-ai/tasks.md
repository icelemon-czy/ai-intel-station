# Implementation Tasks

## 1. Tests

- [x] 1.1 验证未配置 `log_dir` 时默认值解析为 repository-local `.state/discovery/`
- [x] 1.2 验证 arbitrary explicit `log_dir` 与旧模板路径仍覆盖默认值
- [x] 1.3 验证 default run、`--status` 与 `--log-list` 使用同一 configured directory
- [x] 1.4 用 sentinel 验证 migration 不移动、改写或额外删除旧 `.ai` log
- [x] 1.5 执行 generated cron stub，验证 fresh repository 会先创建 state directory 再启动 discovery
- [x] 1.6 验证 Web run 使用 payload config 的 explicit `log_dir`
- [x] 1.7 验证 embedded/checked-in example、schedule、Web source 与 built bundle 同步
- [x] 1.8 验证 `.state/` 与 legacy `.ai` runtime path 均保持 ignored

## 2. Runtime

- [x] 2.1 更新 discovery default、config template 与 schedule helper
- [x] 2.2 修正 Web run 的 config-derived `log_dir`
- [x] 2.3 更新 Web source 与 checked-in static bundle
- [x] 2.4 将 `.state/` 加入 ignore boundary并保留 legacy ignore

## 3. Context And Documentation

- [x] 3.1 更新 README、daily discovery docs 与 L1/L2 的 `.compass` 指向
- [x] 3.2 更新 L5 traceability，只标记实际验证的 evidence
- [x] 3.3 扫描新 context 与 product source，确认没有 runtime `.ai` dependency
