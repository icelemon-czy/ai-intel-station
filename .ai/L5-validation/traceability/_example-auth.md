# Traceability — auth (EXAMPLE)

> 这是一个**填好的示例**，展示追溯文件应该长什么样。实际项目把 `auth` 换成真正的能力域名。
> 模板在 `_domain-template.md`。

## 概要

| 指标 | 数值 |
|:-----|:-----|
| Requirement 总数 | 3 |
| Scenario 总数 | 7 |
| ✅ verified | 5 (71%) |
| ⚠️ partial | 1 (14%) |
| ⚠️ untested | 1 (14%) |
| ❌ unimplemented | 0 |

## Scenario × Code × Test

| Requirement | Scenario | 实现代码 | 测试 | 状态 |
|:------------|:---------|:---------|:-----|:-----|
| REQ-001 用户登录 | 正常登录 | `src/auth/login.ts:handleLogin` | `tests/auth/login.test.ts:45 "normal login"` | ✅ verified |
| REQ-001 用户登录 | 空密码 | `src/auth/login.ts:validatePassword` | `tests/auth/login.test.ts:78 "reject empty password"` | ✅ verified |
| REQ-001 用户登录 | 密码错误 | `src/auth/login.ts:handleLogin` | `tests/auth/login.test.ts:92 "wrong password 401"` | ✅ verified |
| REQ-001 用户登录 | 连续失败锁定 | `src/auth/lockout.ts:checkLockout` | `tests/auth/lockout.test.ts:30` | ⚠️ partial — 只覆盖 3 次，缺 5+ 次边界 |
| REQ-002 Token 刷新 | Token 过期自动刷新 | `src/auth/refresh.ts` | `tests/auth/refresh.test.ts:12` | ✅ verified |
| REQ-002 Token 刷新 | Refresh token 失效跳登录 | `src/auth/refresh.ts:onRefreshFail` | — | ⚠️ untested |
| REQ-003 登出 | 正常登出清理 session | `src/auth/logout.ts` | `tests/auth/logout.test.ts:8` | ✅ verified |

## 已知缺口（引用到变更）

- `REQ-001 连续失败锁定` 5+ 次边界 → 待 `changes/lockout-hardening/` 补齐
- `REQ-002 Refresh token 失效跳登录` → 待 `changes/refresh-fallback/` 覆盖

## 反模式检查（对照 /review-tests 7 条）

| 测试文件:行 | 反模式 | 备注 |
|:-----------|:-------|:-----|
| — | — | 最近一次 /review-tests 未发现命中 |
