# Phase 5 — Deferred items log

Pre-existing issues discovered while executing 05-01 but out of scope per
SCOPE BOUNDARY (Rule 1-3 apply only to files directly modified by the
current task).

## 2026-05-24 — Plan 05-01

- 75 ruff violations remain in `packages/server` (mostly C416 dict
  comprehensions, I001 import-sort, F401 unused imports). All files
  touched by 05-01 are clean. Wider sweep should be a dedicated cleanup
  plan or wave-0 task in a future phase; do NOT fold into in-flight
  feature work.
- `packages/server/keenyspace_server/compile/loop_detector.py` is now a
  thin re-export shim. Existing test files
  (`test_compile_loop_detector.py`, `eval/test_adversarial_fixtures.py`)
  still import from the old path via the shim. Wave 2+ should consider
  migrating those imports to `keenyspace_shared.loop_detector` and
  deleting the shim once no in-repo importer remains.
