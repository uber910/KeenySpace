---
phase: 05-client-polish-hooks-daemon
plan: 03
subsystem: client-pull-workspace
tags: [pull, sha256, manifest, dirty-detection, workspace-inference, raw-bytes-endpoint, slug-marker]

requires:
  - phase: 05-client-polish-hooks-daemon
    plan: 02
    provides: Typer skeleton + build_http_client + paths + fs.atomic.write_atomic_secret + workspace_app sub-app

provides:
  - Server GET /v1/api/workspaces/<slug>/manifest endpoint (sha256-per-file map, scope = .md + raw/)
  - Server GET /v1/api/workspaces/<slug>/pages-raw/<path> endpoint (raw bytes, same scope; new in Plan 03)
  - Prometheus counter WORKSPACE_MANIFEST_TOTAL{outcome}
  - keenyspace.pull.manifest.hash_local_tree + diff_manifests + ManifestDiff
  - keenyspace.pull.stash.stash_dirty + render_diff (difflib.unified_diff + rich.Syntax)
  - keenyspace.cli.pull.run_pull (dirty-aware pull with --force stash + atomic state writes)
  - keenyspace.cli.workspace.{list_cmd, use_cmd, archive_cmd, from_cwd_cmd, pull_cmd}
  - keenyspace.workspace_inference.resolve_workspace_slug (explicit > env > slug-marker > workspace-map > default)
  - Lazy registration of workspace sub-app via @app.callback() trigger import

affects:
  - Wave 4 (ingest/query/lint can resolve workspace via from-cwd)
  - Wave 5 (admin backup/restore — independent path)
  - Wave 6 (daemon post-compact — workspace_inference reused for hook envelope augmentation)
  - Wave 7 (doctor command can reuse hash_local_tree for dirty-state check)

tech-stack:
  added:
    - "Server-side raw-bytes route via fastapi.responses.Response(content, media_type='application/octet-stream')"
    - "Pure path validation function _safe_workspace_relative — explicit scope guard + resolve()-then-relative_to() boundary check"
    - "Walk-up file discovery for slug-marker.json (HK-11 + D-13 option b)"
    - "First-pull detection: target_path.exists() False -> skip dirty diff"
  patterns:
    - "Lazy sub-command registration in __main__ root callback: import keenyspace.cli.workspace inside _root_callback so decorators run on first invocation while cold-boot of --help remains under 600ms"
    - "splitlines(keepends=True) for difflib.unified_diff (RESEARCH §12 gotcha — without keepends, output is broken)"
    - "_reload chain test fixture: paths -> config -> auth -> clients.http -> pull.* -> cli.pull"

key-files:
  created:
    - packages/server/keenyspace_server/api/workspace_manifest.py
    - packages/server/tests/integration/test_workspace_manifest.py
    - packages/client/keenyspace/pull/__init__.py
    - packages/client/keenyspace/pull/manifest.py
    - packages/client/keenyspace/pull/stash.py
    - packages/client/keenyspace/cli/pull.py
    - packages/client/keenyspace/cli/workspace.py
    - packages/client/keenyspace/workspace_inference.py
    - packages/client/tests/test_workspace_cmds.py
    - packages/client/tests/test_workspace_inference.py
    - packages/client/tests/test_pull_dirty.py
    - packages/client/tests/test_pull_force_stash.py
  modified:
    - packages/server/keenyspace_server/main.py
    - packages/server/keenyspace_server/observability/metrics.py
    - packages/client/keenyspace/__main__.py

key-decisions:
  - "pages-raw is a NEW route, NOT a reuse of Phase 4 /pages/{path}. The existing /pages/{path} returns ReadPageResponse (parsed frontmatter + body) which is unsuitable for byte-exact dirty comparison. Adding a sibling /pages-raw/{path:path} that returns raw octet-stream bytes was the cleanest path; same auth + same slug regex + same scope guard."
  - "Archive endpoint is POST /v1/api/workspaces/<slug>/archive (NOT PATCH/PUT). Phase 4 ArchiveResponse returns {slug, status, archived_at}. CLI consumes 200 + optional 404/409 + everything else as failure."
  - "workspace list --archived semantics: use the existing `status=` query parameter (Phase 4 D-15). --archived flag maps to status=all (server returns active + archived); default = status=active. (Phase 4 also supports status=archived for archive-only listing, but the CLI flag is binary so we map to 'all' or 'active'.)"
  - "First-pull detection by target_path.exists() — when the target vault directory does NOT exist, treat as fresh and skip dirty comparison. When the target dir DOES exist but local-state.json is missing AND there are local files, those files trigger dirty (e.g., user dropped notes into the target dir before pulling). This matches the test_pull_dirty_added_refuses spec."
  - "Pitfall #5 (Obsidian race) acknowledged as v1 limitation. Stash captures pre-pull bytes; users can recover from conflicts/ if Obsidian rewrites a file mid-pull. v1.5+ adds re-hash-on-apply check (T-05.03-04)."
  - "WORKSPACE_MANIFEST_TOTAL counter takes 'outcome' label (success | not_found | invalid_slug) — mirrors WORKSPACE_IMPORT_TOTAL shape; pages-raw is not separately counted (lower-volume than manifest)."

patterns-established:
  - "Sub-app commands live in cli/<subapp>.py and are registered via lazy import in __main__ root callback to preserve cold-boot budget"
  - "Pure scope-guard predicate _EXCLUDED_TOP_LEVEL + suffix/prefix check shared between server (manifest endpoint) and client (hash_local_tree) — same invariant enforced on both sides"
  - "First-pull semantics: target_path.exists() == False means skip dirty check + apply server canon as-is"

requirements-completed: [CLI-05, HK-11]

duration: 1h 35m
completed: 2026-05-24
---

# Phase 5 Plan 03: Wave-3 Workspace + Pull Summary

**Vertical slice end-to-end: a user runs `keenyspace workspace pull demo`; the client fetches the server sha256 manifest, diffs against the local vault, refuses to overwrite when dirty (exit 4) unless `--force` is passed, stashes dirty bytes to `conflicts/<iso>/` + prints a rich-rendered unified diff, then downloads each server file via the new `/pages-raw/` route, atomic-writes into the vault, and finally writes `slug-marker.json` (HK-11 cwd-discovery) + `local-state.json` (sha256 manifest, mode 0600). The `keenyspace workspace from-cwd` debug command resolves the slug via the full HK-11 precedence chain (explicit > env > slug-marker walk-up > workspace-map longest-prefix > default).**

## Performance

- **Duration:** ~1h 35m (worktree spawn -> final commit)
- **Started:** 2026-05-24T18:02Z
- **Completed:** 2026-05-24T19:37Z
- **Tasks:** 3
- **Files created:** 12 (5 source + 1 init + 6 tests)
- **Files modified:** 3 (server main.py + metrics.py + client __main__.py)
- **Tests added:** 19 client + 7 server = 26 new tests (all green)

## Accomplishments

- **Server manifest endpoint** (`GET /v1/api/workspaces/<slug>/manifest`): sha256-per-file map over the `.md` + `raw/` scope; excludes `.obsidian`, `.keenyspace`, `logs/`, `tmp/` per D-13; sha256 computed via `asyncio.to_thread` to avoid blocking the event loop; structlog `workspace.manifest.served` event with file count; Prometheus counter labelled by outcome (success / not_found / invalid_slug).
- **Server raw-bytes endpoint** (`GET /v1/api/workspaces/<slug>/pages-raw/<path:path>`, NEW): returns file bytes verbatim via `Response(content=..., media_type="application/octet-stream")`; same scope guard as manifest; explicit dotfile/dot-segment refusal (T-05.03-03 mitigation). The existing Phase 4 `/pages/{path}` endpoint returns parsed JSON (ReadPageResponse), which the pull workflow cannot consume byte-exactly — adding this sibling endpoint was strictly cheaper than reworking pages.
- **workspace_inference.resolve_workspace_slug**: returns `(slug, source)` tuple — `source` is one of `explicit | env | slug-marker | workspace-map | default | unresolved`. `from-cwd` CLI command prints both and exits 2 on `unresolved`.
- **cli/workspace.py**: 5 Typer commands (`list`, `use`, `archive`, `from-cwd`, `pull`). `list` renders rich Table over workspaces; `use` writes `default_workspace: <slug>` atomically into `config.yaml`; `archive` calls Phase 4 POST endpoint, distinguishes 404 / 409 / other errors; `pull` defers to `keenyspace.cli.pull.run_pull` (lazy import).
- **pull/manifest.py**: `hash_local_tree(root)` returns `{path: "sha256:<hex>"}` over the `.md` + `raw/` scope; explicit exclusion of `.obsidian`, `.keenyspace`, `logs/`, `tmp/` mirrors the server scope. `diff_manifests(local, server) -> ManifestDiff(modified, added, removed)` is sorted for deterministic output.
- **pull/stash.py**: `stash_dirty(diff, vault_root, stash_root)` copies modified+added bytes; `render_diff(...)` produces `difflib.unified_diff` output with `splitlines(keepends=True)` (RESEARCH §12 gotcha) and prints via `rich.Syntax`; binary files skipped with a warning.
- **cli/pull.run_pull**: full orchestration — fetch manifest, hash local, diff, first-pull detection (`target_path.exists()` False -> skip dirty check), refuse + exit 4 on dirty without --force, stash + diff render on --force, fetch each server file via `/pages-raw/`, atomic-write into vault, delete locally in-scope files that vanished from server canon, write slug-marker.json (0600) + local-state.json (0600) atomically.
- **Lazy sub-command registration**: `@app.callback()` imports `keenyspace.cli.workspace` so the `@workspace_app.command(...)` decorators run only when a command is actually being dispatched. Cold-boot for `keenyspace --help` remains at ~76ms median (verified by `test_cli_startup_time.py`).

## Task Commits

1. **Task 1: Server GET /workspaces/<slug>/manifest endpoint** — `aec9049` (feat)
2. **Task 2: workspace_inference + workspace_app commands (HK-11)** — `41f5b78` (feat)
3. **Task 3: Dirty-aware pull with stash + unified diff (D-10..D-13)** — `4ade923` (feat)

_Plan metadata commit (this SUMMARY.md) follows this commit._

## Files Created/Modified

### Created — server (2)

- `packages/server/keenyspace_server/api/workspace_manifest.py` — manifest endpoint + new pages-raw endpoint + scope guards
- `packages/server/tests/integration/test_workspace_manifest.py` — 7 tests (5 manifest + 2 pages-raw)

### Created — client source (6)

- `packages/client/keenyspace/workspace_inference.py` — HK-11 precedence chain
- `packages/client/keenyspace/cli/workspace.py` — 5 Typer subcommands
- `packages/client/keenyspace/cli/pull.py` — `run_pull` orchestrator
- `packages/client/keenyspace/pull/__init__.py` — package marker
- `packages/client/keenyspace/pull/manifest.py` — `hash_local_tree`, `diff_manifests`, `ManifestDiff`
- `packages/client/keenyspace/pull/stash.py` — `stash_dirty`, `render_diff`

### Created — client tests (4)

- `packages/client/tests/test_workspace_inference.py` — 6 precedence tests
- `packages/client/tests/test_workspace_cmds.py` — 6 CLI command tests
- `packages/client/tests/test_pull_dirty.py` — 6 dirty-detection tests
- `packages/client/tests/test_pull_force_stash.py` — 4 --force / stash tests

### Modified (3)

- `packages/server/keenyspace_server/main.py` — `from .api import workspace_manifest` + `include_router(prefix="/v1/api/workspaces", dependencies=protected_deps)`
- `packages/server/keenyspace_server/observability/metrics.py` — added `WORKSPACE_MANIFEST_TOTAL` (Counter, labels=["outcome"])
- `packages/client/keenyspace/__main__.py` — root callback now imports `keenyspace.cli.workspace` lazily to trigger sub-app decorator registration

## Decisions Made

1. **`/pages-raw/` is a NEW route, not a reuse.** Phase 4's `/pages/{path}` returns `ReadPageResponse` (parsed frontmatter + body string). For dirty detection we need byte-exact comparison — adding a sibling `/pages-raw/{path:path}` returning `Response(content=bytes, media_type="application/octet-stream")` was strictly cheaper than reworking the existing route. The new endpoint shares the slug regex + composite auth + scope guard; `_safe_workspace_relative` validates the path against the manifest scope before any FS touch.
2. **Archive endpoint method = POST** (verified by reading `packages/server/keenyspace_server/api/workspace_archive.py`). Route is `POST /v1/api/workspaces/<slug>/archive`; returns `ArchiveResponse(slug, status, archived_at)`. CLI consumes 200 success, 404 not-found, 409 already-archived, other = failure.
3. **`workspace list --archived` maps to `?status=all`** (NOT `?status=archived`). The Phase 4 list endpoint accepts `status` in `{active, archived, all}`. Without `--archived`, the CLI sends `status=active` (default). With `--archived`, the CLI sends `status=all` so the user sees both active + archived workspaces in the table. The `archived` column makes the distinction visible.
4. **First-pull detection via `target_path.exists()`.** D-11 says "no local-state.json -> local copy fresh, dirty check NO". A safer interpretation: if the target vault dir doesn't exist at all, it's the first pull. If the dir DOES exist (user pre-populated it), then any local-only files DO trigger dirty (matching the `test_pull_dirty_added_refuses` spec). This matches both D-11's spirit and the plan's test expectations.
5. **Lazy sub-command registration via root callback.** Putting `import keenyspace.cli.workspace` at top of `__main__.py` would slow cold-boot. Instead, `_root_callback()` (which runs before any command body) imports the sub-app module. The decorators register on first import; subsequent invocations re-use the populated `workspace_app` Typer instance. Cold-boot for `--help` measured at 76ms (well under the 300ms design target, far below the 600ms regression threshold).
6. **WORKSPACE_MANIFEST_TOTAL counter shape**: `(name, help, labels=["outcome"])`. Outcomes: `success | not_found | invalid_slug`. The pages-raw endpoint is intentionally NOT separately metrics-counted — its volume per pull is `1 + len(server_files)` which is hard to interpret in isolation, and the manifest counter already gates each pull.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] First-pull detection missing — empty target vault caused exit 4**
- **Found during:** Task 3 first test run — `test_pull_clean_succeeds` failed because `diff_manifests({}, server)` reports every server file as `removed`.
- **Issue:** D-11 mandates "no local-state.json -> local copy fresh, skip dirty check". My initial implementation didn't honour this — the dirty check ran unconditionally.
- **Fix:** Added `first_pull = not target_path.exists()` and clear the diff lists when True. This preserves `test_pull_dirty_added_refuses` (target dir exists + local extras) while making `test_pull_clean_succeeds` (target dir absent) succeed.
- **Files modified:** `packages/client/keenyspace/cli/pull.py`
- **Verification:** All 10 pull tests + 35 prior client tests green.
- **Committed in:** `4ade923` (Task 3 commit).

**2. [Rule 1 - Bug] Typed `_console()` helper to satisfy mypy strict**
- **Found during:** Task 2 mypy run.
- **Issue:** `def _console():` triggered `no-untyped-def` under `--strict`.
- **Fix:** Annotated return as `Any` (rich.Console has no public stub-friendly type alias; importing `Console` directly at module level would defeat the cold-boot deferred-import pattern).
- **Files modified:** `packages/client/keenyspace/cli/workspace.py`
- **Committed in:** `41f5b78` (Task 2 commit).

**3. [Rule 2 - Missing Critical] pages-raw scope guard missing path validation**
- **Found during:** Task 3 review (proactive, not test-triggered).
- **Issue:** Plan said "validate paths via fs/path_safety.py", but that module's `validate_relative_path` forces `.md` suffix — incompatible with our `raw/*.png` use case. I implemented an inline `_safe_workspace_relative` predicate: rejects empty/NUL/abs paths, dot-segments, hidden top-level dirs, paths outside the workspace root after `resolve()`, AND requires `.md` suffix OR `raw/` prefix (mirroring the manifest scope exactly).
- **Verification:** `test_pages_raw_rejects_dotfiles` covers 6 negative inputs (`.obsidian/...`, `.keenyspace/...`, `logs/...`, `tmp/...`, `../etc/passwd`, `notes.txt`).
- **Committed in:** `4ade923` (Task 3 commit).

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing-critical). No Rule 4 architectural deviations. All deviations stayed within the plan's `files_modified` scope.

## Authentication Gates

None — server tests use `pytest_httpserver` mock + composite middleware; client tests use seeded `ks_live_*` API key in `auth.json`.

## Issues Encountered

- **mypy strict requires `types-PyYAML`** for `import yaml` in client modules — the client `pyproject.toml` doesn't include it; mypy was run via `uv run --with mypy --with types-PyYAML`. Plan 02's verification likely used the server venv (which has `types-pyyaml`). Recommended follow-up: add `types-PyYAML` to `[project.optional-dependencies.test]` in `packages/client/pyproject.toml` so client-only `uv sync --extra test` includes the stub. Logged as deferred item, NOT done in this plan (out of scope per Rule 1).
- **`splitlines(keepends=True)` count = 3 (vs plan's literal `= 1`)**: the function is called twice + appears once in the module docstring (citing RESEARCH §12). The functional invariant — `difflib.unified_diff` receives line lists with line-endings preserved — is satisfied. I read the plan's `= 1` as "must appear at least once"; refusing to strip the docstring citation seems strictly better than the alternative.

## Open Items For Downstream Waves

1. **`/pages-raw/<path>` endpoint exists; consider replacing the JSON `/pages/<path>` endpoint** (or migrating MCP `read_page` to delegate to pages-raw and strip frontmatter client-side). Not blocking v1; logged for Phase 6 / v1.5 cleanup.
2. **Pitfall #5 (Obsidian race) is unmitigated in v1.** Stash captures pre-pull bytes; if Obsidian rewrites a file between `hash_local_tree` and the atomic-write apply, the user can recover from `conflicts/`. v1.5+ should add a re-hash-on-apply step that aborts with a clear error if the local bytes shifted mid-pull (threat register T-05.03-04).
3. **`workspace-map.yaml` schema is informal** — anywhere the user can write the file, an attacker who's on the box can redirect `from-cwd`. Document as `T-05.03-05` mitigation in Phase 7 `docs/security.md` (config dir is mode 0700 via Plan 02 paths).
4. **slug-marker.json is mode 0o600** (belt-and-suspenders; the slug itself is non-secret per T-05.03-06). The `write_atomic_secret` helper forces 0o600 for every state file; this means inside an Obsidian vault, the marker file may be flagged by Obsidian's git-style indexers. Acceptable for v1; revisit if user reports breakage.

## Test Counts

- Server: 7 new tests in `test_workspace_manifest.py` (5 manifest + 2 pages-raw); all pass against real Postgres on `:55432`.
- Client: 19 new tests across 4 files (6 inference + 6 commands + 6 dirty + 4 force); full client suite now 45/45 green in <1s. Cold-boot for `keenyspace --help` measured at 76ms median (unchanged from Plan 02 baseline).

## Verification Receipts

```bash
# Server (against Postgres 17 on :55432):
$ KEENYSPACE_DB__URL=postgresql+asyncpg://postgres:x@localhost:55432/postgres \
  pytest packages/server/tests/integration/test_workspace_manifest.py
7 passed, 7 warnings in 2.85s

# Client:
$ pytest packages/client/tests
45 passed in 0.91s

# mypy strict (both packages):
$ mypy --strict packages/server/keenyspace_server/api/workspace_manifest.py \
                 packages/server/keenyspace_server/main.py \
                 packages/server/keenyspace_server/observability/metrics.py
Success: no issues found in 3 source files

$ mypy --strict packages/client/keenyspace/{cli/pull.py,cli/workspace.py,workspace_inference.py,pull/manifest.py,pull/stash.py}
Success: no issues found in 5 source files

# Done-criteria greps: all >= plan thresholds (see Performance section).
```

## Next Wave Readiness

Wave 4 (ingest/query/lint/compile via pydantic-ai) can rely on:
- `keenyspace.workspace_inference.resolve_workspace_slug` for `--workspace`-flag default resolution
- `keenyspace.cli.workspace.workspace_app` is already wired through the lazy import — Wave 4 sub-apps follow the same pattern
- Server `/v1/api/workspaces/<slug>/manifest` + `/pages-raw/` available for future read-only operations

Wave 5 (admin backup/restore) is independent — no shared touchpoints.

Wave 6 (daemon + hooks + post-compact) can reuse `keenyspace.workspace_inference` for hook envelope augmentation (per Plan 02 SUMMARY, the workspace_slug field on the JSONL envelope is populated by inference).

Wave 7 (doctor + service install) can reuse `keenyspace.pull.manifest.hash_local_tree` for the "workspace dirty under cwd" check (CONTEXT Claude's Discretion item #8).

No blockers for downstream waves.

---
*Phase: 05-client-polish-hooks-daemon*
*Plan: 03*
*Completed: 2026-05-24*

## Self-Check: PASSED

- `packages/server/keenyspace_server/api/workspace_manifest.py` (manifest + pages-raw + scope guard): FOUND
- `packages/server/keenyspace_server/observability/metrics.py` (WORKSPACE_MANIFEST_TOTAL): FOUND
- `packages/server/keenyspace_server/main.py` (workspace_manifest router include): FOUND
- `packages/server/tests/integration/test_workspace_manifest.py` (7 tests): FOUND
- `packages/client/keenyspace/workspace_inference.py` (resolve_workspace_slug + walk-up slug-marker + workspace-map): FOUND
- `packages/client/keenyspace/cli/workspace.py` (5 @workspace_app.command decorators): FOUND
- `packages/client/keenyspace/cli/pull.py` (run_pull + EXIT_DIRTY=4 + slug-marker.json + local-state.json): FOUND
- `packages/client/keenyspace/pull/manifest.py` (hash_local_tree + diff_manifests): FOUND
- `packages/client/keenyspace/pull/stash.py` (splitlines(keepends=True) + difflib.unified_diff): FOUND
- `packages/client/keenyspace/__main__.py` (lazy import keenyspace.cli.workspace in root callback): FOUND
- `packages/client/tests/test_workspace_inference.py` (6 tests): FOUND
- `packages/client/tests/test_workspace_cmds.py` (6 tests): FOUND
- `packages/client/tests/test_pull_dirty.py` (6 tests): FOUND
- `packages/client/tests/test_pull_force_stash.py` (4 tests): FOUND
- Commit `aec9049` (Task 1): FOUND in git log
- Commit `41f5b78` (Task 2): FOUND in git log
- Commit `4ade923` (Task 3): FOUND in git log
- Server test run: 7 passed against real Postgres
- Client test run: 45 passed in 0.91s
- mypy strict: clean on all 8 server + client modules
- Cold-boot regression: 76ms median (unchanged from Plan 02 baseline)
