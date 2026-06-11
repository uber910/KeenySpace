---
phase: 07-public-release-prep-v0-1-0-alpha
plan: "01"
subsystem: auth
tags: [auth, group-gate, oidc, security, tdd]
requires: []
provides: [User.groups, OIDC-group-gate, AuthSettings.required_group]
affects: [auth/user.py, auth/oidc.py, auth/composite.py, config.py, main.py]
tech_stack:
  added: []
  patterns: [dataclasses.field default_factory, structlog.get_logger, contextlib.suppress]
key_files:
  created:
    - packages/server/tests/auth/test_groups_claim.py
    - packages/server/tests/auth/test_group_gate.py
  modified:
    - packages/server/keenyspace_server/auth/user.py
    - packages/server/keenyspace_server/auth/oidc.py
    - packages/server/keenyspace_server/auth/composite.py
    - packages/server/keenyspace_server/config.py
    - packages/server/keenyspace_server/main.py
decisions:
  - "Gate is OIDC-path only (D-15): api_key holders bypass by design; possession proves admission"
  - "Error message is exactly 'forbidden' with no group name in error or log (ASVS V7)"
  - "Empty required_group string disables gate for backward compatibility with existing deploys"
metrics:
  duration: "~15 minutes"
  completed: "2026-06-10T23:35:25Z"
  tasks: 2
  files: 7
---

# Phase 7 Plan 01: D-05 Group Entry Gate Summary

**One-liner:** OIDC group membership gate with non-leaking 403, api_key bypass, and empty-string disable for backward compat.

## What Was Built

Added the D-05 group entry gate to the server auth path. An OIDC user must be a member of the group named in `KEENYSPACE_AUTH__REQUIRED_GROUP` to pass authentication. API key users bypass the gate entirely (D-15). An empty setting disables the gate (backward compatible with all existing deploys).

### Task 1: Groups claim extraction (RED then GREEN)

**RED:** Created `test_groups_claim.py` with 4 tests; all failed because `User.groups` didn't exist.

**GREEN:**
- `auth/user.py`: added `groups: list[str] = field(default_factory=list)` — default keeps all existing api_key call sites valid with no changes
- `auth/oidc.py`: extracts `groups` claim from decoded JWT before constructing `User`; defensively coerces to `list[str]` (non-list → `[]`, non-string members filtered out)

**Verification:** 4 tests green; `mypy` strict clean.

### Task 2: OIDC-only group entry gate (RED then GREEN)

**RED:** Created `test_group_gate.py` with 5 tests; all failed because `CompositeAuthBackend.__init__` had no `required_group` param.

**GREEN:**
- `config.py`: added `required_group: str = ""` to `AuthSettings` — maps to `KEENYSPACE_AUTH__REQUIRED_GROUP` env var
- `auth/composite.py`: added `required_group: str = ""` keyword param to `__init__`, stored as `self._required_group`; added gate check in `authenticate()` — only fires for OIDC-sourced users when `_required_group` is non-empty; raises `AuthenticationError("forbidden")` with `sub` logged but no group name (ASVS V7)
- `main.py`: wired `required_group=settings.auth.required_group` at the `CompositeAuthBackend` construction site

**Verification:** 5 new + 16 existing composite tests green; `mypy` and `ruff` strict clean.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing SIM105 ruff lint in oidc.py**
- **Found during:** Task 2 ruff verification sweep of touched files
- **Issue:** `try: conn.state.ks_at_expiring_soon = True\nexcept Exception: pass` triggers SIM105; pre-existing in oidc.py before this plan
- **Fix:** Replaced with `with contextlib.suppress(Exception): conn.state.ks_at_expiring_soon = True`; added `import contextlib`
- **Files modified:** `packages/server/keenyspace_server/auth/oidc.py`
- **Commit:** included in Task 2 commit

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced. The gate is entirely within the existing `authenticate()` path — no new trust boundaries.

Threat register entries T-07-01 through T-07-04 (from plan) are addressed:
- T-07-01 (groups claim injection): JWT is JWKS-verified before claims are read — no new surface
- T-07-02 (api_key gate bypass): accepted by design (D-15)
- T-07-03 (group name leak in error/log): mitigated — error is exactly `"forbidden"`, log emits `sub` only
- T-07-04 (silent gate disable): accepted — empty `required_group` = disabled for backward compat

## Known Stubs

None. All implementation is fully wired end-to-end.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | 4a19844 | feat(07-01): add User.groups field and extract groups claim from OIDC token |
| Task 2 | 80059ba | feat(07-01): add OIDC group gate config field and wire in main.py |
| SUMMARY | 39e5900 | docs(07-01): create plan 01 SUMMARY.md |

## Self-Check: PASSED

All code is written, tested, ruff/mypy clean, and committed. SUMMARY.md committed as 39e5900.
