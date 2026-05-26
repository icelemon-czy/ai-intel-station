# Implementation Tasks

## 1. Tests

- [x] 1.1 为统一 workspace command surface 编写测试，覆盖 `collect`、`query`、`briefing`、`backfill` 四类入口
- [x] 1.2 为 briefing through operator surface 编写测试，验证缺失来源时仍继续并显式标注缺口

## 2. Workspace Surface

- [x] 2.1 新建统一 operator surface 模块与根级运行入口
- [x] 2.2 将 collect / query / briefing / backfill 接到统一入口，并保留现有输出语义

## 3. Documentation And Validation

- [x] 3.1 更新根级运行文档，使统一 operator surface 成为唯一主入口
- [x] 3.2 更新 traceability 与 session 记录，反映 operator surface 已落地
