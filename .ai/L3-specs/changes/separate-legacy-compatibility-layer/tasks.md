# Implementation Tasks

## 1. Tests

- [x] 1.1 为入口拓扑编写测试，验证统一入口存在且旧 wrapper 路径不再作为运行时依赖
- [x] 1.2 为迁移后的 collect/query/briefing/backfill 编写测试，验证运行时不依赖旧入口文件

## 2. Entrypoint Migration

- [x] 2.1 将旧入口的运行时职责迁入统一 operator surface
- [x] 2.2 删除或停用旧 wrapper 代码路径，并同步迁移受影响测试

## 3. Packaging And Layout

- [x] 3.1 建立统一的根级打包/运行配置
- [x] 3.2 更新目录职责文档，明确不再保留并行旧入口表面
