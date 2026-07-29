# Implementation Tasks

## 1. CI Boundary

- [x] 1.1 Skill lint 以 `.agents/skills` 为 canonical source
- [x] 1.2 core gate 安装 `dev` extra 并 broad-discover non-WeChat tests
- [x] 1.3 optional WeChat gate 安装 `dev,wechat` 并运行 WeChat unit/runtime tests
- [x] 1.4 Web gate 独立运行 clean install、build 与全部 Node tests

## 2. HTTP Test Reliability

- [x] 2.1 fixed ports 改为 kernel-assigned free ports
- [x] 2.2 subprocess 等待真实 readiness，不把 pre-bind banner 当成功
- [x] 2.3 multi-item fixture 可重复创建 shared directory

## 3. Spec-Aligned Assertions

- [x] 3.1 navigation、briefing metadata/content、Collect error assertion 对齐 main Spec
- [x] 3.2 copy/capitalization 不作为 behavior contract
- [x] 3.3 UTC saved timestamp 无 deprecated API warning

## 4. Validation

- [x] 4.1 core Python、runner、optional WeChat、Web、build gates 全绿
- [x] 4.2 更新 L2/L5 evidence 并完成 review/archive
