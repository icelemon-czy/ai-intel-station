# L3 Spec → Real end-to-end test coverage

Each row maps one requirement from
[`.ai/L3-specs/specs/system.md`](specs/system.md) to the **real**
end-to-end tests that exercise it. "Real" means the test
exercises the actual public surface a user hits in production
— `serve_workspace` running in a real subprocess, `requestJson`
issuing real HTTP, `subprocess.run(["gh", ...])` looking up the
real `PATH` — without stubbing the business layer.

On sandboxes that block `bind(2)` / `connect(2)`, the cross-process
HTTP tests in `tests/test_l3_http_e2e.py` self-skip. On developer
machines and CI the whole stack runs end-to-end.

## How to run the L3 e2e surface

```bash
.venv/bin/python -m unittest \
  tests.test_e2e_archive \
  tests.test_l3_http_e2e \
  tests.test_l3_requirements \
  tests.test_l3_subspec_e2e \
  tests.test_l3_subspec_remaining_e2e \
  tests.test_l3_policy_meta
```

## What "real" means here

For an L3 test to count as "real", the policy enforced by
`tests/test_l3_policy_meta.py` is:

1. **No `monkeypatch.setattr(<business_module>, ...)`** replacing
   the whole of `run_gh`, `save_repo`, `fetch_repo`,
   `fetch_papers_by_category`, `save_papers`, `fetch_article`,
   `run_collect`, or `run_web_workspace` with a fake.
2. **No `patch.object(server, "do_GET")`** over the WorkspaceHandler.
3. **Network-layer substitution IS allowed**: a fake `gh` shell
   script on PATH, or `urllib.request.urlopen` redirected to a
   local file. These are network-layer changes, not business.

See `test_l3_policy_meta.py` for the regex-enforced version.
