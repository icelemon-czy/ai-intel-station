# Delta Spec: research-web-collect-persistence

> **变更来源**: align-web-collect-with-local-output-truth
> **Delta 类型**: ADDED Requirements（补充到 research-web-collect 能力域）
> **创建**: 2026-05-27

## ADDED Requirements

### WEB-COLLECT-PERSIST-01 — GitHub 单 repo 落盘目标

Web collect GitHub（单 repo 模式）MUST write files to the workspace real `output/github/` directory, NOT to `/tmp/output`.

### WEB-COLLECT-PERSIST-02 — Papers 必须落盘

Web collect papers MUST call `save_papers()` after fetching, writing to `output/papers/`. Fetch-only (in-memory) responses are forbidden.

### WEB-COLLECT-PERSIST-03 — WeChat 必须完成异步调用

Web collect WeChat MUST properly execute `fetch_article()` as an async function (via `asyncio.run()`). Returning a coroutine object without awaiting is forbidden.

### WEB-COLLECT-PERSIST-04 — output_root 参数化

`run_collect(source, fields)` MUST accept an optional `output_root: Path` parameter. When provided, all source handlers MUST use it as the base for their output directories. When omitted, MUST default to the workspace `output/` directory.

### WEB-COLLECT-PERSIST-05 — Server 透传 output_root

`server.py` POST `/api/collect/run` MUST pass the server's configured `output_root` to `run_collect()`.

## WHEN / THEN Scenarios

### Scenario 1: GitHub repo collect writes to real output root

```
GIVEN output_root = tmp_path / "output"
WHEN  run_collect("github", {"query": "owner/repo", "search": False, "max": 10}, output_root=output_root)
THEN  save_repo is called with output_dir == output_root / "github"
AND   result["status"] == "success"
```

### Scenario 2: Papers collect saves to real output root

```
GIVEN output_root = tmp_path / "output"
  AND fetch_papers_by_category returns 2 paper dicts
WHEN  run_collect("papers", {"category": "cs.AI", "max": 2}, output_root=output_root)
THEN  save_papers is called with (papers, "cs.AI", output_root / "papers")
AND   result["status"] == "success"
AND   result["saved_count"] == 2
```

### Scenario 3: WeChat collect properly runs async fetch

```
GIVEN output_root = tmp_path / "output"
  AND fetch_article is an async function
WHEN  run_collect("wechat", {"url": "https://mp.weixin.qq.com/s/test"}, output_root=output_root)
THEN  fetch_article is executed (not just called), called with (url, output_dir=output_root / "wechat")
AND   result["status"] == "success"
```

### Scenario 4: Backward compatibility — no output_root needed by caller

```
GIVEN run_collect is called without output_root
WHEN  run_collect("github", {"query": "owner/repo", "search": False, "max": 10})
THEN  no TypeError is raised
AND   result["status"] is either "success" or "error" (not an uncaught exception)
```
