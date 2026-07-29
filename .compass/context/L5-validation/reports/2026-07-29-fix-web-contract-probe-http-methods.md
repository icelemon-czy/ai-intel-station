# Web Contract Probe HTTP Method 修复报告

## 结论

Web full-stack contract probe 现在验证 frontend 实际使用的 HTTP method、path 与最小
valid input，不再把 POST action 统一当作 GET。built bundle 中的 15 个 API literal
与 15 个 request descriptor 必须一一对应；新增、删除或改名 endpoint 会让 coverage
assertion 失败。

本次是 test oracle defect，没有修改 product code 或 Web behavior Spec。

## Red Evidence

```text
bundled-node --test web/test/fullstack.contract.test.mjs
2 passed, 1 failed
endpoint /api/briefing/preview returned 404
```

backend 的 `/api/briefing/preview` 只处理 POST，frontend 也以 POST 调用；旧 probe
硬编码 GET，因此 failure 不能证明 route 缺失。若只修第一处，它还会在需要 query
parameter 的 detail、preview 与 discovery job route 继续产生 false failure。

## Green Evidence

```text
bundled-node --test web/test/fullstack.contract.test.mjs
3 passed, 0 failed, 0 skipped

bundled-node --test web/test/fullstack.real_e2e.test.mjs
5 passed, 0 failed, 0 skipped
```

两组 test 均在允许 loopback socket 的环境中运行真实 Python subprocess server。

## Test Boundary

- GET route 使用 valid dynamic query；Library detail 与 Markdown preview 读取 test-owned
  ResearchItem sidecar。
- briefing preview/save 使用 POST；save 只写 temporary output root。
- collect POST 使用 intentional unknown source，验证 route 与 response shape，不触发 remote。
- discover POST 使用不存在的 isolated config，background task 不触发 remote。
- unknown discovery job 允许 route-specific 404，但必须返回 `unknown job`，从而与
  unknown API path 的 404 区分。
- process exit 删除 temporary output tree。

## Traceability

- Web Workspace traceability 补充 method-aware real backend integration evidence。
- 对应 test：`web/test/fullstack.contract.test.mjs`。
