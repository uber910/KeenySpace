---
phase: 07-public-release-prep-v0-1-0-alpha
plan: 10
subsystem: ci/deploy/docs
tags: [drill, backup-restore, ci, release-readiness, security]
dependency_graph:
  requires: [07-08]
  provides: [green-drill-ci-path, honest-release-readiness]
  affects: [.github/workflows/drill.yml, deploy/scripts/backup-restore-drill.sh, docs/RELEASE-READINESS.md]
tech_stack:
  added: []
  patterns: [chmod-600-after-jq-write, overridable-compose-var, honest-doc-versioning]
key_files:
  created: []
  modified:
    - .github/workflows/drill.yml
    - deploy/scripts/backup-restore-drill.sh
    - docs/RELEASE-READINESS.md
decisions:
  - chmod 600 via explicit post-write call (not umask) — grep-verifiable and unambiguous
  - DRILL_COMPOSE_FILES uses bash parameter expansion default (:-) for unset-safe override
  - RELEASE-READINESS updated to honest pending state without false-green claim
metrics:
  duration: 15min
  completed: "2026-06-14"
  tasks: 3
  files: 3
---

# Phase 7 Plan 10: Drill CI Blocker Closure Summary

Three independent blockers prevented the `backup-restore-drill` job from exiting green on every run. This plan closes all three with targeted, minimal edits and corrects the RELEASE-READINESS.md claims that overstated the drill's CI readiness.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | chmod 600 auth.json at both write sites (CR-01) | 5adea98 | `.github/workflows/drill.yml` |
| 2 | KEENYSPACE_SERVER_URL + DRILL_COMPOSE_FILES overlay (CR-02 + CR-03) | bb59b93 | `.github/workflows/drill.yml`, `deploy/scripts/backup-restore-drill.sh` |
| 3 | Re-align RELEASE-READINESS C3/REL-07 with fixed state (WR-05) | 3a59922 | `docs/RELEASE-READINESS.md` |

## What Was Done

**CR-01 (Task 1):** The runner default umask (022) causes a bare `jq ... > auth.json` to write at mode 0644. The client's `_validate_auth_file_mode` in `auth.py:37` checks `mode & 0o077` and raises `AuthFileModeError` on the first CLI call. Added `chmod 600 "$HOME/.config/keenyspace/auth.json"` immediately after each of the two jq writes in `drill.yml`: once in the primary "Mint API key" step (line 56), once inside the single-quoted reauth heredoc body (line 86, executed verbatim by `/tmp/drill-reauth.sh` at reauth time).

**CR-02 (Task 2A):** `ClientSettings` in `config.py` uses `env_prefix="KEENYSPACE_"` and declares `server_url: str` with no default. Without `KEENYSPACE_SERVER_URL` in the environment, pydantic raises `ValidationError` before any HTTP request is attempted by `keenyspace backup` or `keenyspace restore`. Added `KEENYSPACE_SERVER_URL: http://localhost:8000` to the "Seed and backup-restore drill" step's `env` block.

**CR-03 (Task 2B):** `backup-restore-drill.sh` line 30 previously hardcoded `COMPOSE="docker compose -f deploy/docker-compose.yml"`. The script performs its own `down -v` + `up -d` cycle internally, meaning the `deploy/docker-compose.drill.yml` overlay (which provides the `blueprints-test` mount for `ks-test-svc`) was lost after the wipe. `/tmp/drill-reauth.sh` then exhausted its 60×3s loop waiting for Authentik to provision the service account that no longer existed. Changed line 30 to `COMPOSE="docker compose ${DRILL_COMPOSE_FILES:--f deploy/docker-compose.yml}"` — the `:-` default keeps the base-only compose for manual/local runs while letting CI inject both files via `DRILL_COMPOSE_FILES: "-f deploy/docker-compose.yml -f deploy/docker-compose.drill.yml"` in the drill step env.

**WR-05 (Task 3):** RELEASE-READINESS.md C3 (line 48) and REL-07 table row (line 81) claimed the destructive drill was "structurally runnable in CI" after 07-08. Re-verification proved that false — the three above blockers made it exit non-zero on every run. Updated both entries to accurately describe the 07-10 blocker closures and retain the honest "final green CI run gates on next tag push" status without false-green claims.

## Deviations from Plan

None — plan executed exactly as written.

## Success Criteria Status

- [x] CR-01 closed: auth.json written at mode 0600 at both sites; no AuthFileModeError
- [x] CR-02 closed: KEENYSPACE_SERVER_URL set; ClientSettings instantiates without ValidationError
- [x] CR-03 closed: drill overlay passed through DRILL_COMPOSE_FILES; test-seed blueprint survives down -v; reauth path unblocked
- [x] WR-05 closed: RELEASE-READINESS C3/REL-07 honest about drill state
- [x] SC3 (REL-07) and SC5 (REL-08) unblocked: backup-restore-drill job can complete green on the next tag push

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The `chmod 600` fix closes the only credential-at-rest concern (T-07-10-01) documented in the plan's threat model. `DRILL_COMPOSE_FILES` is confined to the drill step env — base/production compose files are unchanged (T-07-10-02 accepted by design).

## Self-Check: PASSED

- `.github/workflows/drill.yml` modified: confirmed (commits 5adea98, bb59b93)
- `deploy/scripts/backup-restore-drill.sh` modified: confirmed (commit bb59b93)
- `docs/RELEASE-READINESS.md` modified: confirmed (commit 3a59922)
- All three commits exist in git log
- No "structurally runnable in CI" remains in RELEASE-READINESS.md
- `chmod 600` count = 2 in drill.yml
- `bash -n` clean on backup-restore-drill.sh
