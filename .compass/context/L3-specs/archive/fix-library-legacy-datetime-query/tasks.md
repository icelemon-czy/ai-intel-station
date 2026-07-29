# Implementation Tasks

## 1. Tests

- [x] 1.1 minute-precision legacy datetime 通过 public Library query/service 返回，不使 request 崩溃
- [x] 1.2 malformed item datetime 在无 date filter 时保留并稳定排序，在有 filter 时被隔离
- [x] 1.3 repository output real round-trip 不再因 legacy datetime 失败

## 2. Library Query

- [x] 2.1 支持 system-produced minute-precision datetime
- [x] 2.2 统一 item-side safe datetime parsing，并让 sort 与 filter 使用相同 boundary

## 3. Validation

- [x] 3.1 运行 datetime、Library service 与 real Web round-trip tests
- [x] 3.2 更新 L5 traceability/report 并完成 review/archive
